from .search_objects import search_objects


def handle_legacy(req_body, headers, config):
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
    return handler(params, headers, config)


def _search_objects(params, headers, config):
    """
    Handler for the "search_objects" RPC method, called by `handle_legacy` above.
    This takes all the API parameters to the legacy api and translates them to
    a call to `search_objects`.
    It also injects any extra info, such as narrative data, for each search result.
    """
    match_filter = params.get('match_filter', {})
    # Match full text for any field in the objects
    text_query = {'match': {'_all': match_filter.get('full_text_in_all', '')}}
    # Base query object for ES. Will get mutated and expanded below.
    query = {'bool': {'must': [text_query]}}
    # Handle a search on tags, which corresponds to the generic `tags` field in all indexes.
    if match_filter.get('source_tags'):
        # If source_tags_blacklist is `1`, then we are **discluding** these tags.
        blacklist_tags = bool(match_filter.get('source_tags_blacklist'))
        tags = match_filter['source_tags']
        # Construct a compound query to match every tag using "term"
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        if blacklist_tags:
            query['bool']['must_not'] = tag_query
        else:
            query['bool']['must'] += tag_query
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
        sort.append({
            prop: {
                'order': 'asc' if sort_rule.get('ascending') else 'desc'
            }
        })
    pagination = params.get('pagination', {})
    access_filter = params.get('access_filter', {})
    with_private = bool(access_filter.get('with_private'))
    with_public = bool(access_filter.get('with_public'))
    search_params = {
        'query': query,
        'size': pagination.get('count', 20),
        'from': pagination.get('start', 0),
        'sort': sort,
        'only_public': not with_private and with_public,
        'only_private': not with_public and with_private
    }
    search_results = search_objects(search_params, headers, config)
    narrative_infos = None
    post_processing = params.get('post_processing', {})
    # TODO post_processing/include_highlight -- need to add on to search_objects
    # TODO post_processing/skip_info,skip_keys,skip_data -- look are results in current api
    # TODO post_processing/ids_only -- look at results in current api
    if post_processing.get('add_narrative_info'):
        narrative_infos = _fetch_narrative_info(search_results, headers, config)
    return _create_search_objects_result(params, search_results, narrative_infos)


def _search_types(params, headers, config):
    """
    Search for the number of objects of each type, matching constraints.
    """


def _get_objects(params, headers, config):
    """
    Retrieve a list of objects based on their ids.
    """


def _list_types(params, headers, config):
    """
    List registered searchable object types.
    """


def _fetch_narrative_info(results, headers, config):
    """
    The legacy api has an option for post_processing/add_narrative_info. If
    this option is `1`, then every search result gets a corresponding narrative
    info tuple attached. For each result object, we construct a single bulk
    query to ES that fetches the narrative data. We then construct that data
    into a "narrative_info" tuple, which contains:
    (narrative_name, object_id, time_last_saved, owner_username, owner_displayname)
    Returns a dictionary of workspace_id mapped to the narrative_info tuple above.
    """
    # TODO get "display name" (eg. auth service call)
    #  for now we just use username
    sources = _get_sources(results)
    workspace_ids = [s['workspace_id'] for s in sources]
    # Every OR boolean clause in the query below
    matches = [
        {'match': {'workspace_id': wsid}}
        for wsid in workspace_ids
    ]
    # ES query params
    search_params = {'query': {'bool': {'should': matches}}}
    # Make the query for narratives on ES
    search_results = search_objects(search_params, headers, config)
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
        infos[int(narr['workspace_id'])] = narr_tuple
    return infos


def _create_search_objects_result(params, search_results, narrative_infos):
    if narrative_infos:
        # TODO interpolate narrative_infos into the results, if present
        # Need to look at current api result to get the format for this
        pass
    result = {
        'pagination': params.get('pagination', {}),
        'sorting_rules': params.get('sorting_rules', []),
        'total': search_results['hits']['total'],
        'search_time': search_results['took'],
        'objects': _get_sources(search_results)
    }
    return result


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
