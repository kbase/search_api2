"""
Implements https://github.com/kbase/KBaseSearchAPI/blob/master/KBaseSearchEngine.spec

PostProcessing type:
    skip_info - disclude 'parent_guid', 'object_name', and 'timestamp'
    skip_keys - disclude all the type-specific keys ('key_props' in the old indexes)
    skip_data - disclude "raw data" for the object ('data' and 'parent_data')
    ids_only - shortcut to mark all three skips as true
    include_highlight - include highlights of fields that matched the query


ObjectData type:
    guid - string - unique id for the doc ('_id' field in our case)
    parent_guid - string - id of a parent if there is a parent object
    object_name - string - name of object
    timestamp - int - save date of object
    parent_data - object - parent data
    data - object - object-specific data
    key_props
    object_props - dict
          general properties for all objects. This mapping contains the keys
          'creator', 'copied', 'module', 'method', 'module_ver', and 'commit' -
          respectively the user that originally created the object, the user
          that copied this incarnation of the object, and the module and method
          used to create the object and their version and version control
          commit hash. Not all keys may be present; if not their values were
          not available in the search data.
    highlight - dict of string to list of string - search result highlights from ES. TODO
          The keys are the field names and the list contains the sections in
          each field that matched the search query. Fields with no hits will
          not be available. Short fields that matched are shown in their
          entirety. Longer fields are shown as snippets preceded or followed by
          "...".
"""
from .search_objects import search_objects
from .utils.config import init_config

_CONFIG = init_config()


def handle_legacy(req_body, headers):
    """
    Handle a JSON RPC request body, making it backwards compatible with the previous Java API.
    """
    method = req_body['method']
    # We want to ignore any leading module name:
    # "KBaseSearchEngine.search_objects" -> "search_objects"
    # "search_objects" -> "search_objects"
    method_short = method.split('.')[-1]
    if method_short not in _HANDLERS:
        raise RuntimeError(f'Unknown method: {method_short}. Available: {list(_HANDLERS.keys())}')
    handler = _HANDLERS[method_short]
    params = req_body['params'][0]
    return handler(params, headers)


def _search_objects(params, headers):
    """
    Handler for the "search_objects" RPC method, called by `handle_legacy` above.
    This takes all the API parameters to the legacy api and translates them to
    a call to `search_objects`.
    It also injects any extra info, such as narrative data, for each search result.
    """
    match_filter = params.get('match_filter', {})
    # Base query object for ES. Will get mutated and expanded below.
    query = {
        'bool': {'must': [], 'must_not': [], 'should': []},
    }  # type: dict
    if match_filter.get('full_text_in_all'):
        # Match full text for any field in the objects
        query['bool']['must'].append({'match': {'_all': match_filter['full_text_in_all']}})
    # Handle a search on tags, which corresponds to the generic `tags` field in all indexes.
    if match_filter.get('source_tags'):
        # If source_tags_blacklist is `1`, then we are **discluding** these tags.
        blacklist_tags = bool(match_filter.get('source_tags_blacklist'))
        tags = match_filter['source_tags']
        # Construct a compound query to match every tag using "term"
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        if blacklist_tags:
            query['bool']['must_not'] += tag_query
        else:
            query['bool']['must'] += tag_query
    # Handle match_filter/lookupInKeys
    query = _handle_lookup_in_keys(match_filter, query)
    # TODO match_filter/exclude_subobjects
    # TODO what is the noindex tag?
    # Handle filtering by object type
    object_types = params.get('object_types', [])
    if object_types:
        query['bool']['should'] = [
            {'term': {'obj_type_name': obj_type}}
            for obj_type in object_types
        ]
    # Handle sorting options
    sorting_rules = params.get('sorting_rules', [])
    sort = []  # type: list
    for sort_rule in sorting_rules:
        if sort_rule.get('is_object_property'):
            prop = sort_rule['property']
        else:
            prop = _SORT_PROP_MAPPING[sort_rule['property']]
        order = 'asc' if sort_rule.get('ascending') else 'desc'
        sort.append({prop: {'order': order}})
    pagination = params.get('pagination', {})
    access_filter = params.get('access_filter', {})
    with_private = bool(access_filter.get('with_private'))
    with_public = bool(access_filter.get('with_public'))
    search_params = {
        'query': query,
        'size': pagination.get('count', 20),
        'from': pagination.get('start', 0),
        'sort': sort,
        'public_only': not with_private and with_public,
        'private_only': not with_public and with_private
    }
    search_results = search_objects(search_params, headers)
    print('results', search_results)
    narrative_infos = None
    post_processing = params.get('post_processing', {})
    if post_processing.get('add_narrative_info'):
        narrative_infos = _fetch_narrative_info(search_results, headers)
    return {
        'pagination': params.get('pagination', {}),
        'sorting_rules': params.get('sorting_rules', []),
        'total': search_results['hits']['total'],
        'search_time': search_results['took'],
        'objects': _get_sources(search_results),
        'access_group_narrative_info': narrative_infos
    }


def _search_types(params, headers):
    """
    Search for the number of objects of each type, matching constraints.
    params:
        match_filter
            full_text_in_all
            object_name
            timestamp
        access_filter
            with_private - boolean - include private objects
            with_public - boolean - include public objects
            with_all_history - ignored
    """


def _get_objects(params, headers):
    """
    Retrieve a list of objects based on their upas.
    params:
        guids - list of string - KBase IDs (upas) to fetch
        post_processing - object of post-query filters (see PostProcessing def at top of this module)
    output:
        objects - list of ObjectData - see the ObjectData type description in the module docstring above.
        search_time - int - time it took to perform the search on ES
        access_group_narrative_info - dict of {access_group_id: narrative_info} -
            Information about the workspaces in which the objects in the
            results reside. This data only applies to workspace objects.
    """
    post_processing = params.get('post_processing', {})
    search_results = search_objects({
        'query': {'terms': {'_id': params['guids']}}
    }, headers)
    # TODO
    objects = _get_object_data_from_search_results(search_results, post_processing)
    narrative_infos = _fetch_narrative_info(search_results, headers)
    return {
        'search_time': search_results['took'],
        'objects': objects,
        'access_group_narrative_info': narrative_infos
    }


def _list_types(params, headers):
    """
    List registered searchable object types.
    params:
        type_name - string - optional - specify the type to get a count for
    if type_name not specified, then all types are counted
    output:
        types - dict - type name mapped to dicts of:
            type_name - string
            type_ui_title - string
            keys - list of dicts - "searchable type keyword"
                dicts are:
                    key_name - string
                    key_ui_title - string
                    key_value_title - string
                    hidden - bool
                    link_key - string
    """
    return {}


def _handle_lookup_in_keys(match_filter, query):
    """
    Handle the match_filter/lookupInKeys option from the legacy API.
    This allows the user to pass a number of field names and term or range values for filtering.
    """
    if not match_filter.get('lookupInKeys'):
        return query
    # This will be a dict where each key is a field name and each val is a MatchValue type
    lookup_in_keys = match_filter['lookupInKeys']
    for (key, match_value) in lookup_in_keys.items():
        # match_value will be a dict with one of these keys set:
        # value (string), int_value, double_value, bool_value, min_int,
        # max_int, min_date, max_date, min_double, max_double.
        # `term_value` will be any term (full equality) match.
        term_value = (match_value.get('value') or
                      match_value.get('int_value') or
                      match_value.get('double_value') or
                      match_value.get('bool_value'))
        # `range_min` and `range_max` will be any values for doing a range query
        range_min = match_value.get('min_int') or match_value.get('min_date') or match_value.get('min_double')
        range_max = match_value.get('max_int') or match_value.get('max_date') or match_value.get('max_double')
        if term_value:
            query_clause = {'match': {key: term_value}}
        elif range_min and range_max:
            query_clause = {'range': {key: {'gte': range_min, 'lte': range_max}}}
        query['bool']['must'].append(query_clause)
    return query


def _get_object_data_from_search_results(search_results, post_processing):
    """
    Construct a list of ObjectData (see the type def in the module docstring at top).
    Uses the post_processing options (see the type def for PostProcessing at top).
    """
    # TODO post_processing/include_highlight -- need to add on to search_objects
    # TODO post_processing/skip_info,skip_keys,skip_data -- look are results in current api
    # TODO post_processing/ids_only -- look at results in current api
    sources = _get_sources(search_results)
    object_data = []  # type: list
    # Keys found in every ws object
    global_keys = ['_id', 'parent_id', 'obj_name', 'timestamp', 'parent_data', 'obj_type_name', 'obj_type_version', 'creator', 'data', 'is_public', 'access_group']  # noqa
    for source in sources:
        obj = {}  # type: ignore
        for key in global_keys:
            obj[key] = source.get(key)
        # The nested 'data' is all object-specific, so disclude all global keys
        obj['data'] = {key: source[key] for key in source if key not in global_keys}
        object_data.append(obj)
    return object_data


def _fetch_narrative_info(results, headers):
    """
    For each result object, we construct a single bulk query to ES that fetches
    the narrative data. We then construct that data into a "narrative_info"
    tuple, which contains: (narrative_name, object_id, time_last_saved,
    owner_username, owner_displayname) Returns a dictionary of workspace_id
    mapped to the narrative_info tuple above.
    """
    # TODO get "display name" (eg. auth service call)
    #  for now we just use username
    sources = _get_sources(results)
    workspace_ids = [s['access_group'] for s in sources]
    # Every OR boolean clause in the query below
    matches = [
        {'match': {'access_group': wsid}}
        for wsid in workspace_ids
    ]
    narrative_index_name = _CONFIG['global']['ws_type_to_indexes']['Narrative']
    # ES query params
    search_params = {
        'query': {'bool': {'should': matches}},
        'indexes': [narrative_index_name]
    }
    # Make the query for narratives on ES
    search_results = search_objects(search_params, headers)
    # Get all the source document objects for each narrative result
    search_data_sources = _get_sources(search_results)
    infos = {}  # type: dict
    for narr in search_data_sources:
        narr_tuple = (
            narr['narrative_title'],
            narr['obj_id'],
            narr['timestamp'],
            narr['creator'],
            narr['creator']  # XXX using username for display name
        )
        infos[int(narr['access_group'])] = narr_tuple
    return infos


def _get_sources(search_results):
    """
    Pull out the _source document data for every search result from ES.
    """
    return [r['_source'] for r in search_results['hits']['hits']]


# Map property names sent to the Java API to the names we actually use in ES
_SORT_PROP_MAPPING = {
    'access_group_id': 'access_group',
    'type': 'obj_type',
    'timestamp': 'timestamp'
}


# RPC method handler index
_HANDLERS = {
    'search_objects': _search_objects,
    'search_types': _search_types,
    'list_types': _list_types,
    'get_objects': _get_objects
}
