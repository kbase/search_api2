from datetime import datetime
import re
import logging

from src.utils.config import init_config
from src.clients.workspace import get_workspace_info, workspace_info_to_dict
from src.clients.user_profile import get_user_profile
from src.search_objects import search_objects


_CONFIG = init_config()
logger = logging.getLogger('searchapi2')


def handle_lookup_in_keys(match_filter, query):
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
                      match_value.get('string_value') or
                      match_value.get('int_value') or
                      match_value.get('double_value') or
                      match_value.get('bool_value'))
        # `range_min` and `range_max` will be any values for doing a range query
        range_min = match_value.get('min_int') or match_value.get('min_date') or match_value.get('min_double')
        range_max = match_value.get('max_int') or match_value.get('max_date') or match_value.get('max_double')
        query_clause = {}  # type: dict
        if term_value:
            query_clause = {'match': {key: term_value}}
        elif range_min or range_max:
            range_query = {}
            if range_min:
                range_query['gte'] = range_min
            if range_max:
                range_query['lte'] = range_max
            query_clause = {'range': {key: range_query}}
        if query_clause:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append(query_clause)
    return query


def _workspace_type_to_alias_mapping():
    type_mapping = _CONFIG['global']['ws_type_to_indexes']
    mapping = {}
    for type_id, alias in type_mapping.items():
        [module_name, type_name] = type_id.split('.')
        mapping[type_name] = alias
    return mapping


_WS_TYPE_TO_ALIAS_MAPPING = _workspace_type_to_alias_mapping()


def workspace_type_to_alias(type_name):
    return _WS_TYPE_TO_ALIAS_MAPPING.get(type_name)


# We abstract the sort fields provided in the spec from the actual
# storage of the sort field.
_SORT_PROPERTY_TO_FIELD_MAPPING = {
    'scientific_name': 'scientific_name.raw',
    'genome_scientific_name': 'genome_scientific_name.raw'
}


def sort_object_property(property_name):
    return _SORT_PROPERTY_TO_FIELD_MAPPING.get(property_name, property_name)


# Mapping of special sorting properties names from the Java API to search2 key names
_SORT_PROP_MAPPING = {
    'access_group_id': 'access_group',
    'type': 'obj_type_name',
    'timestamp': 'timestamp'
}


def sort_common_property(name):
    return _SORT_PROP_MAPPING.get(name)


def get_genome_features_index_name():
    index_name = _CONFIG['global']['genome_features_current_index_name']
    return _CONFIG['global']['latest_versions'][index_name]


def iso8601_to_epoch(time_string):
    return round(datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S%z').timestamp())

# Extract and transform search results.


# TODO: I don't get what a guid is if it is not the global identifier for an object
# in the search indexes.
def get_guid_from_doc(doc):
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


# Mappings from search2 document fields to search1 fields.
# Only where different
KEY_MAPPING = {
    'obj_name': 'object_name',
    'obj_type_name': 'type',
}


def get_object_data_from_search_results(search_results, post_processing):
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
        for (search2_key, search1_key) in KEY_MAPPING.items():
            obj[search1_key] = source.get(search2_key, search1_key)
        # The nested 'data' is all object-specific, so disclude all global keys
        obj['data'] = {key: source[key] for key in source if key not in KEY_MAPPING}
        # Set some more top-level data manually that we use in the UI

        obj['guid'] = get_guid_from_doc(result)

        # TODO: what is kbase_id? An object ref? If so, perhaps
        # we can just build it out of the usual fields. I don't remember
        # kbase_id from the original search, but maybe it was there...
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

        # Disabled this for now.
        # It is a nice thought to replace detail fields with match highlights, but
        # highlights are sometimes truncated. So we can do some comparison of the
        # strings after stripping out the highlighting markers (em tag, but this is
        # configurable, so we need to keep that in mind)
        # Handle the highlighted field data, converting field names, if necessary
        # if result.get('highlight'):
        #     hl = result['highlight']
        #     obj['highlight'] = {}
        #     for key in result['highlight']:
        #         if key in _KEY_MAPPING:
        #             search2_key = _KEY_MAPPING[key]
        #             obj[search2_key] = hl[key]
        #         else:
        #             obj[key] = hl[key]
        # else:
        #     obj['highlight'] = {}

        highlight = result.get('highlight', {})
        transformed_highlight = {}
        # Replace field names (keys) with the field names from the search1 api.
        for key, value in highlight.items():
            transformed_highlight[KEY_MAPPING.get(key, key)] = value
        obj['highlight'] = transformed_highlight

        object_data.append(obj)
    return object_data


def get_object_data_from_search_results2(search_results, post_processing):
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
        for (search2_key, search1_key) in KEY_MAPPING.items():
            obj[search1_key] = source.get(search2_key, search1_key)
        # The nested 'data' is all object-specific, so disclude all global keys
        obj['data'] = {key: source[key] for key in source if key not in KEY_MAPPING}
        # Set some more top-level data manually that we use in the UI

        obj['guid'] = get_guid_from_doc(result)

        # TODO: what is kbase_id? An object ref? If so, perhaps
        # we can just build it out of the usual fields. I don't remember
        # kbase_id from the original search, but maybe it was there...
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

        # Disabled this for now.
        # It is a nice thought to replace detail fields with match highlights, but
        # highlights are sometimes truncated. So we can do some comparison of the
        # strings after stripping out the highlighting markers (em tag, but this is
        # configurable, so we need to keep that in mind)
        # Handle the highlighted field data, converting field names, if necessary
        # if result.get('highlight'):
        #     hl = result['highlight']
        #     obj['highlight'] = {}
        #     for key in result['highlight']:
        #         if key in _KEY_MAPPING:
        #             search2_key = _KEY_MAPPING[key]
        #             obj[search2_key] = hl[key]
        #         else:
        #             obj[key] = hl[key]
        # else:
        #     obj['highlight'] = {}

        highlight = result.get('highlight', {})
        transformed_highlight = {}
        # Replace field names (keys) with the field names from the search1 api.
        for key, value in highlight.items():
            transformed_highlight[KEY_MAPPING.get(key, key)] = value
        obj['highlight'] = transformed_highlight

        object_data.append(obj)
    return object_data


def fetch_narrative_info(results, auth):
    """
    For each result object, construct a single bulk query to ES that fetches
    the narrative data. Then construct that data into a "narrative_info"
    tuple, which contains: (narrative_name, object_id, time_last_saved,
    owner_username, owner_displayname) Returns a dictionary of workspace_id
    mapped to the narrative_info tuple above.

    This also returns a dictionary of workspace infos for each object:
    (id, name, owner, save_date, max_objid, user_perm, global_perm, lockstat, metadata)
    """
    # TODO get "display name" (eg. auth service call)
    #  for now we just use username
    hit_docs = [hit['doc'] for hit in results['hits']]
    # TODO workspace timestamp

    # Early exit if no sources ... um, we can just inspect the length of sources, no?
    # Note that by definition, each search hit corresponds to a unique workspace.
    workspace_ids = []
    ws_infos = {}
    owners = set()
    for hit_doc in hit_docs:
        workspace_id = hit_doc['access_group']
        workspace_ids.append(workspace_id)
        workspace_info = get_workspace_info(workspace_id, auth)
        owners.add(workspace_info[2])

        ws_infos[str(workspace_id)] = workspace_info

    if len(workspace_ids) == 0:
        return ({}, {})

    # Get profile for all owners
    user_profiles = get_user_profile(list(owners), auth)
    user_profile_map = {profile['user']['username']: profile for profile in user_profiles}

    # TODO: shouldn't we use an alias here and not the actual index?
    narrative_index_name = _CONFIG['global']['ws_type_to_indexes']['KBaseNarrative.Narrative']

    # ES query params
    search_params = {
        'indexes': [narrative_index_name],
        'size': len(workspace_ids)
    }  # type: dict

    # This is how we select only the requested narratives.
    matches = [
        {'match': {'access_group': wsid}}
        for wsid in workspace_ids
    ]

    # The search_objects function expects any custom search constraints to be provided
    # in the query key. (Not to be confused with the ES 'query' key)
    search_params['query'] = {
        'bool': {
            'should': matches
        }
    }

    # Fetch the narratives from ES
    search_results = search_objects(search_params, {
        'Authorization': auth
    })

    # Get all the source document objects for each narrative result
    narrative_hits = [hit['doc'] for hit in search_results['hits']]

    narr_infos = {}

    for narr in narrative_hits:
        # Note the improved return structure.
        id = narr['access_group']
        [workspace_id, workspace_name, owner, moddate,
         max_objid, user_permission, global_permission,
         lockstat, ws_metadata] = ws_infos[str(id)]

        narr_infos[str(id)] = {
            'type': 'narrative',
            'title': narr.get('narrative_title'),
            'modified_at': narr.get('modified_at'),
            'permission': user_permission,
            'is_public': global_permission == 'r',
            'owner': {
                'username': owner,
                'realname': user_profile_map[owner]['user']['realname']
            }
        }

    # For objects without a narrative, look up the workspace and determine what it's all about.
    for id in workspace_ids:
        if id not in narr_infos:
            [workspace_id, workspace_name, owner, moddate,
             max_objid, user_permission, global_permission,
             lockstat, ws_metadata] = ws_infos[str(id)]

            narr_infos[str(id)] = {
                'type': 'workspace',
                'title': workspace_name,
                'modified_at': iso8601_to_epoch(moddate),
                'permission': user_permission,
                'is_public': global_permission == 'r',
                'owner': {
                    'username': owner,
                    'realname': user_profile_map[owner]['user']['realname']
                }
            }

    return (ws_infos, narr_infos)


def fetch_workspaces_info(results, auth):
    """
    For each result object, construct a single bulk query to ES that fetches
    the narrative data. Then construct that data into a "narrative_info"
    tuple, which contains: (narrative_name, object_id, time_last_saved,
    owner_username, owner_displayname) Returns a dictionary of workspace_id
    mapped to the narrative_info tuple above.

    This also returns a dictionary of workspace infos for each object:
    (id, name, owner, save_date, max_objid, user_perm, global_perm, lockstat, metadata)
    """
    # TODO get "display name" (eg. auth service call)
    #  for now we just use username
    hit_docs = [hit['doc'] for hit in results['hits']]
    # TODO workspace timestamp

    # Early exit if no sources ... um, we can just inspect the length of sources, no?
    # Note that by definition, each search hit corresponds to a unique workspace.
    workspace_ids = []
    workspaces = []
    owners = set()
    for hit_doc in hit_docs:
        workspace_id = hit_doc['access_group']
        workspace_ids.append(workspace_id)
        workspace_info = workspace_info_to_dict(get_workspace_info(workspace_id, auth))
        owners.add(workspace_info['owner'])

        metadata = workspace_info.get('metadata', {})
        if 'searchtags' in metadata:
            search_tags = metadata.get('searchtags', '').split(' ')
            if 'refdata' in search_tags:
                ws_type = 'refdata'
            elif 'narrative' in search_tags:
                ws_type = 'narrative'
            elif 'narrative' in metadata:
                ws_type = 'narrative'
            else:
                ws_type = 'workspace'
        else:
            if 'narrative' in metadata:
                ws_type = 'narrative'
            else:
                ws_type = 'workspace'

        workspaces.append({
            'ws_info': workspace_info,
            'type': ws_type
        })

    if len(workspace_ids) == 0:
        return {}

    # Get profile for all owners
    user_profiles = get_user_profile(list(owners), auth)
    user_profile_map = {profile['user']['username']: profile for profile in user_profiles}

    # TODO: shouldn't we use an alias here and not the actual index?
    narrative_index_name = _CONFIG['global']['ws_type_to_indexes']['KBaseNarrative.Narrative']

    # ES query params
    search_params = {
        'indexes': [narrative_index_name],
        'size': len(workspace_ids)
    }  # type: dict

    # This is how we select only the requested narratives.
    matches = [
        {'match': {'access_group': wsid}}
        for wsid in workspace_ids
    ]

    # The search_objects function expects any custom search constraints to be provided
    # in the query key. (Not to be confused with the ES 'query' key)
    search_params['query'] = {
        'bool': {
            'should': matches
        }
    }

    # Fetch the narratives from ES
    search_results = search_objects(search_params, {
        'Authorization': auth
    })

    # Get all the source document objects for each narrative result
    narrative_hits = [hit['doc'] for hit in search_results['hits']]

    narr_infos = {}

    for narr in narrative_hits:
        narr_infos[narr['access_group']] = narr

    # For objects without a narrative, look up the workspace and determine what it's all about.
    for workspace in workspaces:
        # More accessible and decorated
        ws_info = workspace['ws_info']
        workspace['info'] = {
            'permission': ws_info['user_permission'],
            'is_public': ws_info['global_permission'] == 'r',
            'modified_at': iso8601_to_epoch(ws_info['modification_date']),
            'owner': {
                'username': ws_info['owner'],
                'realname': user_profile_map[ws_info['owner']]['user']['realname']
            }
        }

        # Per workspace-type info
        if workspace['type'] == 'narrative':
            narr_info = narr_infos.get(ws_info['id'])
            if narr_info is None:
                logger.error(f'workspace {ws_info["id"]} is a Narrative, but Narrative not indexed')
                # TODO: this fakes a narrative, but we need to handle this better.
                narr = {
                    'title': '** Not indexed **'
                }
            else:
                narr = {
                    'title': narr_info.get('narrative_title', 'n/a')
                }
            workspace['narrative'] = narr
        elif workspace['type'] == 'refdata':
            refdata_source = workspace['ws_info'].get('metadata', {}).get('refdata_source', 'n/a')
            workspace['refdata'] = {
                'title': refdata_source,
                'source': refdata_source
            }
        elif workspace['type'] == 'workspace':
            workspace['other'] = {
                'title': workspace['ws_info']['name']
            }

    ws_map = {str(ws['ws_info']['id']): ws for ws in workspaces}
    return ws_map


def get_search_params(params):
    """
    Construct object search parameters from a set of legacy request parameters.
    """
    match_filter = params.get('match_filter', {})
    # Base query object for ES. Will get mutated and expanded below.
    # query = {'bool': {'must': [], 'must_not': [], 'should': []}}  # type: dict
    query = {'bool': {}}  # type: dict

    # Free text search over the "agg_fields" index field.
    if match_filter.get('full_text_in_all'):
        # Match full text for any field in the objects
        query['bool']['must'] = []
        query['bool']['must'].append({'match': {'agg_fields': match_filter['full_text_in_all']}})

    # Search on a specific object_name
    if match_filter.get('object_name'):
        query['bool']['must'] = query['bool'].get('must', [])
        query['bool']['must'].append({'match': {'obj_name': str(match_filter['object_name'])}})

    # Search by timestamp range.
    if match_filter.get('timestamp'):
        ts = match_filter['timestamp']
        # TODO: we just need to support one ... hey, how about 'min'????
        min_ts = ts.get('min_date') or ts.get('min_int') or ts.get('min_double')
        max_ts = ts.get('max_date') or ts.get('max_int') or ts.get('max_double')
        if min_ts and max_ts:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append({'range': {'timestamp': {'gte': min_ts, 'lte': max_ts}}})
        else:
            raise RuntimeError("Invalid timestamp range in match_filter/timestamp.")

    # Handle a search on tags, which corresponds to the generic `tags` field in all indexes.
    # Note that the positive match uses a filter, since we don't need weighting for tag filtering.
    if match_filter.get('source_tags'):
        tags = match_filter['source_tags']
        blacklist_tags = bool(match_filter.get('source_tags_blacklist'))
        # Construct a compound query to match every tag using "term"
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        if blacklist_tags:
            query['bool']['must_not'] = tag_query
        else:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'] += tag_query

    # Handle match_filter/lookupInKeys
    query = handle_lookup_in_keys(match_filter, query)

    # Handle filtering by object type
    indexes = []
    object_types = params.get('object_types', [])
    if object_types:
        # For this fake type, we search on the specific index instead (see lower down).
        type_blacklist = ['GenomeFeature']
        # query['bool']['must'] = query['bool'].get('must', [])

        for object_type in object_types:
            if object_type in type_blacklist:
                continue
            # query['bool']['must'].append({'term': {'obj_type_name': object_type}})
            alias = workspace_type_to_alias(object_type)
            if alias:
                indexes.append(alias)
            else:
                raise ValueError(f'Type "{object_type}" does not map to an alias')

    # Handle sorting options
    sorting_rules = params.get('sorting_rules', [])
    sort = []  # type: list
    for sort_rule in sorting_rules:
        if sort_rule.get('is_object_property'):
            # This mode used to indicate that the sort field is
            # under the data field. Now it just means different
            # processing of the field.
            prop = sort_object_property(sort_rule['property'])
        else:
            prop = sort_common_property(sort_rule['property'])

        # TODO: currently this will silently fail if the sort field is not
        # indicated as an object property
        if prop:
            order = 'asc' if sort_rule.get('ascending') else 'desc'
            sort.append({prop: {'order': order}})

    access_filter = params.get('access_filter', {})
    with_private = bool(access_filter.get('with_private'))
    with_public = bool(access_filter.get('with_public'))
    pagination = params.get('pagination', {})
    # Get excluded index names (handles `exclude_subobjects`)
    search_params = {
        'query': query,
        'from': pagination.get('start', 0),
        'size': pagination.get('count', 20),
        'sort': sort,
        'public_only': not with_private and with_public,
        'private_only': not with_public and with_private
    }

    # TODO: should this not be the alias and not the index name?
    if 'GenomeFeature' in object_types:
        indexes.append(get_genome_features_index_name())

    if len(indexes):
        search_params['indexes'] = indexes

    return search_params


def get_search_params2(params):
    """
    Construct object search parameters from a set of legacy request parameters.
    """
    match_filter = params.get('match_filter', {})
    # Base query object for ES. Will get mutated and expanded below.
    # query = {'bool': {'must': [], 'must_not': [], 'should': []}}  # type: dict
    query = {'bool': {}}  # type: dict

    # Free text search over the "agg_fields" index field.
    if match_filter.get('search_term'):
        # Match full text for any field in the objects
        query['bool']['must'] = []
        query['bool']['must'].append({'match': {'agg_fields': match_filter['search_term']}})

    # Search on a specific object_name
    if match_filter.get('object_name'):
        query['bool']['must'] = query['bool'].get('must', [])
        query['bool']['must'].append({'match': {'obj_name': str(match_filter['object_name'])}})

    # Search by timestamp range.
    if match_filter.get('timestamp'):
        ts = match_filter['timestamp']
        # TODO: we just need to support one ... hey, how about 'min'????
        min_ts = ts.get('min_date') or ts.get('min_int') or ts.get('min_double')
        max_ts = ts.get('max_date') or ts.get('max_int') or ts.get('max_double')
        if min_ts and max_ts:
            query['bool']['must'] = query['bool'].get('must', [])
            query['bool']['must'].append({'range': {'timestamp': {'gte': min_ts, 'lte': max_ts}}})
        else:
            raise RuntimeError("Invalid timestamp range in match_filter/timestamp.")

    # Handle a search on tags, which corresponds to the generic `tags` field in all indexes.
    # Note that the positive match uses a filter, since we don't need weighting for tag filtering.
    if match_filter.get('tags'):
        tags = match_filter['tags']
        # Construct a compound query to match every tag using "term"
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        query['bool']['filter'] = query['bool'].get('filter', [])
        query['bool']['filter'] += tag_query

    if match_filter.get('not_tags'):
        tags = match_filter['not_tags']
        # Construct a compound query to match every tag using "term"
        tag_query = [{'term': {'tags': tag}} for tag in tags]
        query['bool']['must_not'] = query['bool'].get('must_not', [])
        query['bool']['must_not'] += tag_query

    # Handle match_filter/lookupInKeys
    query = handle_lookup_in_keys(match_filter, query)

    # Handle filtering by object type
    indexes = []
    object_types = params.get('object_types', [])
    if object_types:
        # For this fake type, we search on the specific index instead (see lower down).
        type_blacklist = ['GenomeFeature']
        # query['bool']['must'] = query['bool'].get('must', [])

        for object_type in object_types:
            if object_type in type_blacklist:
                continue
            # query['bool']['must'].append({'term': {'obj_type_name': object_type}})
            alias = workspace_type_to_alias(object_type)
            if alias:
                indexes.append(alias)
            else:
                raise ValueError(f'Type "{object_type}" does not map to an alias')

    # Handle sorting options
    sorting_rules = params.get('sorting_rules', [])
    sort = []  # type: list
    for sort_rule in sorting_rules:
        if sort_rule.get('is_object_property'):
            # This mode used to indicate that the sort field is
            # under the data field. Now it just means different
            # processing of the field.
            prop = sort_object_property(sort_rule['property'])
        else:
            prop = sort_common_property(sort_rule['property'])

        # TODO: currently this will silently fail if the sort field is not
        # indicated as an object property
        if prop:
            order = 'asc' if sort_rule.get('ascending') else 'desc'
            sort.append({prop: {'order': order}})

    access_filter = params.get('access_filter', {})
    with_private = bool(access_filter.get('with_private'))
    with_public = bool(access_filter.get('with_public'))
    # Get excluded index names (handles `exclude_subobjects`)
    search_params = {
        'query': query,
        'size': params.get('limit', 20),
        'from': params.get('offset', 0),
        'sort': sort,
        'public_only': not with_private and with_public,
        'private_only': not with_public and with_private
    }

    # TODO: should this not be the alias and not the index name?
    if 'GenomeFeature' in object_types:
        indexes.append(get_genome_features_index_name())

    if len(indexes):
        search_params['indexes'] = indexes

    return search_params


def refs_to_doc_ids(refs):
    doc_ids = []
    for ref in refs:
        if ref.get('ref'):
            reflist = ref.get('ref').split('/')
            wsid = reflist[0]
            objid = reflist[1]
        else:
            wsid = ref.get('workspace_id')
            objid = ref.get('object_id')
        doc_id = f'WS::{wsid}:{objid}'
        doc_ids.append(doc_id)
    return doc_ids


def guids_to_doc_ids(guids):
    doc_ids = []
    # TODO: scrub guids
    for guid in guids:
        doc_ids.append(guid)
    return doc_ids
