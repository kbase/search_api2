"""
RPC methods for the legacy API handler.

Quick type references:

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
import re

from src.methods.search_objects import search_objects as _search_objects
from src.utils.config import init_config

_CONFIG = init_config()

_GENOME_FEATURES_IDX_NAME = _CONFIG['global']['latest_versions'][_CONFIG['global']['genome_features_current_index_name']]  # noqa

# Mappings from search2 document fields to search1 fields:
_KEY_MAPPING = {
    'obj_name': 'object_name',
    'access_group': 'access_group',
    'obj_id': 'obj_id',
    'version': 'version',
    'timestamp': 'timestamp',
    'obj_type_name': 'type',
    # 'obj_type_version': 'type_ver',
    'creator': 'creator'
}

# Mapping of special sorting properties names from the Java API to search2 key names
_SORT_PROP_MAPPING = {
    'access_group_id': 'access_group',
    'type': 'obj_type_name',
    'timestamp': 'timestamp'
}


def search_objects(params, auth):
    """
    Handler for the "search_objects" RPC method, called by `handle_legacy`.
    This takes all the API parameters to the legacy api and translates them to
    a call to `search_objects`.
    It also injects any extra info, such as narrative data, for each search result.
    """
    # KBase convention is to wrap params in an array
    print('xyz params', params)
    params = params[0]
    search_params = _get_search_params(params)
    if params.get('include_highlight'):
        search_params['highlight'] = {'*': {}}
    search_results = _search_objects(search_params, auth)
    post_processing = params.get('post_processing', {})
    (narrative_infos, ws_infos) = _fetch_narrative_info(search_results, auth)
    objects = _get_object_data_from_search_results(search_results, post_processing)
    return {
        'pagination': params.get('pagination', {}),
        'sorting_rules': params.get('sorting_rules', []),
        'total': search_results['count'],
        'search_time': search_results['search_time'],
        'objects': objects,
        'access_group_narrative_info': narrative_infos,
        'access_groups_info': ws_infos
    }


def search_types(params, auth):
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
    output:
        type_to_count - dict where keys are type names and vals are counts
        search_time - int - total time performing search
    This method constructs the same search parameters as `search_objects`, but
    aggregates results based on `obj_type_name`.
    """
    # KBase convention is to wrap params in an array
    params = params[0]
    search_params = _get_search_params(params)
    # Create the aggregation clause using a 'terms aggregation'
    search_params['aggs'] = {
        'type_count': {
            'terms': {'field': 'obj_type_name'}
        }
    }
    search_params['size'] = 0
    search_results = search_objects(search_params, auth)
    # Now we need to convert the ES result format into the API format
    search_time = search_results['search_time']
    buckets = search_results['aggregations']['type_count']['counts']
    counts_dict = {}  # type: dict
    for count_obj in buckets:
        counts_dict[count_obj['key']] = counts_dict.get(count_obj['key'], 0)
        counts_dict[count_obj['key']] += count_obj['count']
    return {
        'type_to_count': counts_dict,
        'search_time': int(search_time)
    }


def get_objects(params, auth):
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
    # KBase convention is to wrap params in an array
    params = params[0]
    post_processing = params.get('post_processing', {})
    search_results = search_objects({'query': {'terms': {'_id': params['guids']}}}, auth)
    objects = _get_object_data_from_search_results(search_results, post_processing)
    (narrative_infos, ws_infos) = _fetch_narrative_info(search_results, auth)
    return {
        'search_time': search_results['search_time'],
        'objects': objects,
        'access_group_narrative_info': narrative_infos,
        'access_groups_info': ws_infos
    }


def server_status(params, auth):
    """
    Example status response from the Java API:
    [{
        "state": "OK",
        "message":"",
        "version":"0.2.2-dev1",
        "git_url":"https://github.com/kbase/KBaseSearchEngine.git",
        "git_commit_hash":"1935768d49d0fe6032a1195de10156d9f319d8ce"}]
    }]
    """
    return {
        'state': 'OK',
        'version': '',
        'message': '',
        'git_url': '',
        'git_commit_hash': ''
    }


def list_types(params, auth):
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
    For now, we're leaving this as a no-op, because we haven't seen this in use
    in KBase codebases anywhere.
    """
    return {}


def _get_search_params(params):
    """
    Construct object search parameters from a set of legacy request parameters.
    """
    match_filter = params.get('match_filter', {})
    # Base query object for ES. Will get mutated and expanded below.
    # query = {'bool': {'must': [], 'must_not': [], 'should': []}}  # type: dict
    query = {'bool': {}}  # type: dict
    if match_filter.get('full_text_in_all'):
        # Match full text for any field in the objects
        query['bool']['must'] = []
        query['bool']['must'].append({'match': {'agg_fields': match_filter['full_text_in_all']}})
    if match_filter.get('object_name'):
        query['bool']['must'] = query['bool'].get('must', [])
        query['bool']['must'].append({'match': {'obj_name': str(match_filter['object_name'])}})
    if match_filter.get('timestamp'):
        ts = match_filter['timestamp']
        min_ts = ts.get('min_date') or ts.get('min_int') or ts.get('min_double')
        max_ts = ts.get('max_date') or ts.get('max_int') or ts.get('max_double')
        if min_ts and max_ts:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append({'range': {'timestamp': {'gte': min_ts, 'lte': max_ts}}})
        else:
            raise RuntimeError("Invalid timestamp range in match_filter/timestamp.")
    # Handle a search on tags, which corresponds to the generic `tags` field in all indexes.
    if match_filter.get('source_tags'):
        # If source_tags_blacklist is `1`, then we are **excluding** these tags.
        blacklist_tags = bool(match_filter.get('source_tags_blacklist'))
        tags = match_filter['source_tags']
        # Construct a compound query to match every tag using "term"
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        if blacklist_tags:
            query['bool']['must_not'] = tag_query
        else:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'] += tag_query
    # Handle match_filter/lookupInKeys
    query = _handle_lookup_in_keys(match_filter, query)
    # Handle filtering by object type
    object_types = params.get('object_types', [])
    if object_types:
        # For this fake type, we search on the specific index instead (see lower down).
        type_blacklist = ['GenomeFeature']
        query['bool']['should'] = [
            {'term': {'obj_type_name': obj_type}}
            for obj_type in object_types
            if obj_type not in type_blacklist
        ]
    # Handle sorting options
    sorting_rules = params.get('sorting_rules', [])
    sort = []  # type: list
    for sort_rule in sorting_rules:
        if sort_rule.get('is_object_property'):
            prop = sort_rule['property']
        elif _SORT_PROP_MAPPING.get(sort_rule['property']):
            prop = _SORT_PROP_MAPPING[sort_rule['property']]
        if prop:
            order = 'asc' if sort_rule.get('ascending') else 'desc'
            sort.append({prop: {'order': order}})
    pagination = params.get('pagination', {})
    access_filter = params.get('access_filter', {})
    with_private = bool(access_filter.get('with_private'))
    with_public = bool(access_filter.get('with_public'))
    # Get excluded index names (handles `exclude_subobjects`)
    search_params = {
        'query': query,
        'size': pagination.get('count', 20),
        'from': pagination.get('start', 0),
        'sort': sort,
        'public_only': not with_private and with_public,
        'private_only': not with_public and with_private
    }
    if 'GenomeFeature' in object_types:
        search_params['indexes'] = [_GENOME_FEATURES_IDX_NAME]
    return search_params


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
        query_clause = {}  # type: dict
        if term_value:
            query_clause = {'match': {key: term_value}}
        elif range_min and range_max:
            query_clause = {'range': {key: {'gte': range_min, 'lte': range_max}}}
        if query_clause:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append(query_clause)
    return query


def _get_object_data_from_search_results(search_results, post_processing):
    """
    Construct a list of ObjectData (see the type def in the module docstring at top).
    Uses the post_processing options (see the type def for PostProcessing at top).
    We translate fields from our current ES indexes to naming conventions used by the legacy API/UI.
    """
    # TODO post_processing/skip_info,skip_keys,skip_data -- look are results in current api
    # TODO post_processing/ids_only -- look at results in current api
    object_data = []  # type: list
    # Keys found in every ws object
    for result in search_results['hits']:
        source = result['doc']
        obj = {}  # type: ignore
        for (search2_key, search1_key) in _KEY_MAPPING.items():
            obj[search1_key] = source.get(search2_key)
        # The nested 'data' is all object-specific, so disclude all global keys
        obj['data'] = {key: source[key] for key in source if key not in _KEY_MAPPING}
        # Set some more top-level data manually that we use in the UI
        obj['key_props'] = obj['data']
        obj['guid'] = _get_guid_from_doc(result)
        obj['kbase_id'] = obj['guid'].strip('WS:')
        idx_pieces = result['index'].split('_')
        idx_name = idx_pieces[0]
        idx_ver = int(idx_pieces[1] or 0) if len(idx_pieces) == 2 else 0
        obj['index_name'] = idx_name
        # obj['index_ver'] = idx_ver
        obj['type_ver'] = idx_ver
        # For the UI, make the type field "GenomeFeature" instead of Genome for features.
        if 'genome_feature_type' in source:
            obj['type'] = 'GenomeFeature'
        # Handle the highlighted field data, converting field names, if necessary
        if result.get('highlight'):
            hl = result['highlight']
            obj['highlight'] = {}
            for key in result['highlight']:
                if key in _KEY_MAPPING:
                    search2_key = _KEY_MAPPING[key]
                    obj[search2_key] = hl[key]
                else:
                    obj[key] = hl[key]
        else:
            obj['highlight'] = {}
        object_data.append(obj)
    return object_data


def _fetch_narrative_info(results, auth):
    """
    For each result object, we construct a single bulk query to ES that fetches
    the narrative data. We then construct that data into a "narrative_info"
    tuple, which contains: (narrative_name, object_id, time_last_saved,
    owner_username, owner_displayname) Returns a dictionary of workspace_id
    mapped to the narrative_info tuple above.

    This also returns a dictionary of workspace infos for each object:
    (id, name, owner, save_date, max_objid, user_perm, global_perm, lockstat, metadata)
    """
    # TODO get "display name" (eg. auth service call)
    #  for now we just use username
    sources = [hit['doc'] for hit in results['hits']]
    # TODO workspace timestamp
    narr_infos = {s['access_group']: (None, None, 0, s.get('creator', ''), s.get('creator', '')) for s in sources}
    ws_infos = {
        s['access_group']: (s['access_group'], '', s.get('creator', ''))
        for s in sources
    }
    workspace_ids = [s['access_group'] for s in sources]
    if not workspace_ids:
        return ({}, {})
    narrative_index_name = _CONFIG['global']['ws_type_to_indexes']['KBaseNarrative.Narrative']
    # ES query params
    search_params = {
        'indexes': [narrative_index_name]
    }  # type: dict
    if workspace_ids:
        # Filter by workspace ID
        matches = [
            {'match': {'access_group': wsid}}
            for wsid in workspace_ids
        ]
        search_params['bool'] = {'should': matches}
    # Make the query for narratives on ES
    search_results = search_objects(search_params, auth)
    # Get all the source document objects for each narrative result
    search_data_sources = [hit['doc'] for hit in search_results['hits']]
    for narr in search_data_sources:
        narr_tuple = (
            narr.get('narrative_title'),
            narr.get('obj_id'),
            narr.get('timestamp'),
            narr.get('creator'),
            narr.get('creator')  # XXX using username for display name
        )
        narr_infos[int(narr['access_group'])] = narr_tuple
    return (narr_infos, ws_infos)


def _get_guid_from_doc(doc):
    """
    Construct a legacy-style "guid" in the form "WS:1/2/3"
    """
    # Remove the first namespace
    _id = doc['id'].replace('WS::', '')
    # Remove any secondary namespace
    _id = re.sub(r'::..::.+', '', _id)
    # Replace colon delimiters with slashes
    _id = _id.replace(':', '/')
    # Add a single-colon delimited workspace namespace
    _id = 'WS:' + _id
    # Append the object version
    ver = str(doc.get('obj_type_version', 1))
    _id = _id + '/' + ver
    return _id
