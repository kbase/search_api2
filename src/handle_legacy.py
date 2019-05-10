from .search_objects import search_objects


def handle_legacy(req_body, headers, config):
    """
    Handle a JSON RPC request body to make it backwards compatible with the old Java API.
    """
    method = req_body['method']
    # "KBaseSearchEngine.search_objects" -> "search_objects"
    # "search_objects" -> "search_objects"
    method_short = method.split('.')[-1]
    handler = _HANDLERS.get(method_short)
    if not handler:
        raise RuntimeError(f'Unknown method: {method_short}. Available: {list(_HANDLERS.keys())}')
    params = req_body['params'][0]
    return handler(params, headers, config)


def _search_objects(params, headers, config):
    match_filter = params.get('match_filter', {})
    text_query = {
        'match': {'_all': match_filter.get('full_text_in_all', '')}
    }
    query = {
        'bool': {
            'must': [text_query]
        }
    }
    if match_filter.get('source_tags'):
        blacklist_tags = bool(match_filter.get('source_tags_blacklist'))
        tags = match_filter['source_tags']
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        if blacklist_tags:
            query['bool']['must_not'] = tag_query
        else:
            query['bool']['must'] += tag_query
    # TODO match_filter/exclude_subobjects -- what does it do?
    # TODO what is the noindex tag?
    object_types = params.get('object_types', [])
    if object_types:
        query['bool']['should'] = [
            {'term': {'obj_type': obj_type}}
            for obj_type in object_types
        ]
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
    # post_processing = params.get('post_processing', {})
    # TODO post_processing/add_narrative_info -- ???
    # TODO post_processing/include_highlight -- need to add on to search_objects
    # TODO post_processing/skip_info,skip_keys,skip_data -- ??? what does it do
    # TODO post_processing/ids_only -- ??? what does it do
    access_filter = params.get('access_filter', {})
    with_private = bool(access_filter.get('with_private'))
    with_public = bool(access_filter.get('with_public'))
    params = {
        'query': query,
        'size': pagination.get('count', 20),
        'from': pagination.get('start', 0),
        'sort': sort,
        'only_public': not with_private and with_public,
        'only_private': not with_public and with_private
    }
    return search_objects(params, headers, config)


# Map property names sent to the Java API to the names we actually use in ES
_SORT_PROP_MAPPING = {
    'access_group_id': 'access_group',
    'type': 'obj_type',
    'timestamp': 'timestamp'
}


# RPC method handler index
_HANDLERS = {
    'search_objects': _search_objects
}
