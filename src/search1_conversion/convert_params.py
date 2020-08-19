"""
Convert RPC params into an Elasticsearch query

Quick type references for the old RPC spec:

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
    highlight - dict of string to list of string - search result highlights from ES
          The keys are the field names and the list contains the sections in
          each field that matched the search query. Fields with no hits will
          not be available. Short fields that matched are shown in their
          entirety. Longer fields are shown as snippets preceded or followed by
          "...".
"""
from src.utils.config import config
from src.utils.obj_utils import get_any
from src.exceptions import ResponseError

# Unversioned feature index name/alias, (eg "genome_features")
_FEATURES_UNVERSIONED = config['global']['genome_features_current_index_name']
# Versioned feature index name (eg "genome_features_2")
_GENOME_FEATURES_IDX_NAME = config['global']['latest_versions'][_FEATURES_UNVERSIONED]

# Mapping of special sorting properties names from the Java API to search2 key names
_SORT_PROP_MAPPING = {
    'scientific_name': 'scientific_name.raw',
    'genome_scientific_name': 'genome_scientific_name.raw',
    'access_group_id': 'access_group',
    'type': 'obj_type_name',
    'timestamp': 'timestamp',
    'guid': 'id',
}


def search_objects(params):
    """
    Convert parameters from the "search_objects" RPC method into an Elasticsearch query.
    """
    query = _get_search_params(params)
    if params.get('include_highlight'):
        # We need a special highlight query so that the main query does not generate
        # highlights for bits of the query which are not user-generated.
        highlight_query = {'bool': {}}
        match_filter = params['match_filter']
        if match_filter.get('full_text_in_all'):
            # Match full text for any field in the objects
            highlight_query['bool']['must'] = [{
                'match': {
                    'agg_fields': match_filter['full_text_in_all']
                }
            }]
        # Note that search_objects, being used by both the legacy and current
        # api, supports highlighting in the generic ES sense, so we pass a
        # valid ES7 highlight param.
        query['highlight'] = {
            'fields': {'*': {}},
            'require_field_match': False,
            'highlight_query': highlight_query
        }
    return query


def search_types(params):
    """
    Convert parameters from the "search_types" RPC method into an Elasticsearch query.
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
    query = _get_search_params(params)
    # Create the aggregation clause using a 'terms aggregation'
    query['aggs'] = {
        'type_count': {
            'terms': {'field': 'obj_type_name'}
        }
    }
    query['size'] = 0
    return query


def get_objects(params):
    """
    Convert params from the "get_objects" RPC method into an Elasticsearch query.
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
    query = {'query': {'terms': {'_id': params['guids']}}}
    return query


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
    if match_filter.get('timestamp') is not None:
        ts = match_filter['timestamp']
        min_ts = ts.get('min_date')
        max_ts = ts.get('max_date')
        if min_ts is not None and max_ts is not None and min_ts < max_ts:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append({'range': {'timestamp': {'gte': min_ts, 'lte': max_ts}}})
        else:
            raise ResponseError(code=-32602, message="Invalid timestamp range in match_filter/timestamp")
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
    if 'sorting_rules' not in params:
        params['sorting_rules'] = [{
          "property": "timestamp",
          "is_object_property": 0,
          "ascending": 1
        }]
    sort = []  # type: list
    for sort_rule in params['sorting_rules']:
        prop = sort_rule.get('property')
        is_obj_prop = sort_rule.get('is_object_property', True)
        ascending = sort_rule.get('ascending', True)
        if not is_obj_prop:
            if prop in _SORT_PROP_MAPPING:
                prop = _SORT_PROP_MAPPING[sort_rule['property']]
            else:
                msg = f"Invalid non-object sorting property '{prop}'"
                raise ResponseError(code=-32602, message=msg)
        order = 'asc' if ascending else 'desc'
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
    Handle the match_filter/lookup_in_keys option from the legacy API.
    This allows the user to pass a number of field names and term or range values for filtering.
    """
    if not match_filter.get('lookup_in_keys'):
        return query
    # This will be a dict where each key is a field name and each val is a MatchValue type
    lookup_in_keys = match_filter['lookup_in_keys']
    for (key, match_value) in lookup_in_keys.items():
        # match_value will be a dict with one of these keys set:
        # value (string), int_value, double_value, bool_value, min_int,
        # max_int, min_date, max_date, min_double, max_double.
        # `term_value` will be any term (full equality) match.
        keys = ['value', 'int_value', 'double_value', 'bool_value']
        term_value = get_any(match_value, keys)
        # `range_min` and `range_max` will be any values for doing a range query
        range_min_keys = ['min_int', 'min_date', 'min_double']
        range_min = get_any(match_value, range_min_keys)
        range_max_keys = ['max_int', 'max_date', 'max_double']
        range_max = get_any(match_value, range_max_keys)
        query_clause: dict = {}
        if term_value:
            query_clause = {'match': {key: term_value}}
        elif range_min is not None or range_max is not None:
            query_clause = {'range': {key: {}}}
            if range_min is not None:
                query_clause['range'][key]['gte'] = range_min
            if range_max is not None:
                query_clause['range'][key]['lte'] = range_max
        if query_clause:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append(query_clause)
    return query
