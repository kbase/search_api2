import re

from src.utils.config import config
from src.utils.formatting import iso8601_to_epoch
from src.utils.user_profiles import get_user_profiles
from src.utils.workspace import get_workspace_info
import src.es_client as es_client

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


def search_objects(params, results, meta):
    """
    Convert Elasticsearch results into the RPC results conforming to the
    "search_objects" method
    """
    post_processing = params.get('post_processing', {})
    (ws_infos, narrative_infos) = _fetch_narrative_info(results, meta)
    objects = _get_object_data_from_search_results(results, post_processing)
    return [{
        'pagination': params.get('pagination', {}),
        'sorting_rules': params.get('sorting_rules', []),
        'total': results['count'],
        'search_time': results['search_time'],
        'objects': objects,
        'access_group_narrative_info': narrative_infos,
        'access_groups_info': ws_infos
    }]


def search_types(params, results, meta):
    """
    Convert Elasticsearch results into RPC results conforming to the spec for
    the "search_types" method.
    """
    # Now we need to convert the ES result format into the API format
    search_time = results['search_time']
    buckets = results['aggregations']['type_count']['counts']
    counts_dict = {}  # type: dict
    for count_obj in buckets:
        counts_dict[count_obj['key']] = counts_dict.get(count_obj['key'], 0)
        counts_dict[count_obj['key']] += count_obj['count']
    return [{
        'type_to_count': counts_dict,
        'search_time': int(search_time)
    }]


def get_objects(params, results, meta):
    """
    Convert Elasticsearch results into RPC results conforming to the spec for
    the "get_objects" method.
    """
    post_processing = params.get('post_processing', {})
    objects = _get_object_data_from_search_results(results, post_processing)
    (ws_infos, narrative_infos) = _fetch_narrative_info(results, meta)
    ret = [{
        'search_time': results['search_time'],
        'objects': objects,
        'access_group_narrative_info': narrative_infos,
        'access_groups_info': ws_infos
    }]
    return ret


def _fetch_narrative_info(results, meta):
    """
    For each result object, we construct a single bulk query to ES that fetches
    the narrative data. We then construct that data into a "narrative_info"
    tuple, which contains: (narrative_name, object_id, time_last_saved,
    owner_username, owner_displayname) Returns a dictionary of workspace_id
    mapped to the narrative_info tuple above.

    This also returns a dictionary of workspace infos for each object:
    (id, name, owner, save_date, max_objid, user_perm, global_perm, lockstat, metadata)
    """
    hit_docs = [hit['doc'] for hit in results['hits']]
    workspace_ids = []
    ws_infos = {}
    owners = set()
    for hit_doc in hit_docs:
        workspace_id = hit_doc['access_group']
        workspace_ids.append(workspace_id)
        workspace_info = get_workspace_info(workspace_id, meta['auth'])
        if len(workspace_info) > 2:
            owners.add(workspace_info[2])
            ws_infos[str(workspace_id)] = workspace_info
    if len(workspace_ids) == 0:
        return ({}, {})
    user_profiles = get_user_profiles(list(owners), meta['auth'])
    user_profile_map = {profile['user']['username']: profile for profile in user_profiles}
    narrative_index_name = config['global']['ws_type_to_indexes']['KBaseNarrative.Narrative']
    # ES query params
    search_params: dict = {
        'indexes': [narrative_index_name],
        'size': len(workspace_ids)
    }
    # Filter by workspace ID
    matches = [
        {'match': {'access_group': wsid}}
        for wsid in workspace_ids
    ]
    search_params['query'] = {
        'bool': {'should': matches}
    }
    # Make the query for narratives on ES
    search_results = es_client.search(search_params, meta)
    # Get all the source document objects for each narrative result
    narrative_hits = [hit['doc'] for hit in search_results['hits']]
    narr_infos = {}
    for narr in narrative_hits:
        # Note the improved return structure.
        _id = narr['access_group']
        if _id not in ws_infos:
            continue
        [workspace_id, workspace_name, owner, moddate,
         max_objid, user_permission, global_permission,
         lockstat, ws_metadata] = ws_infos[str(_id)]
        narr_infos[str(_id)] = [
            '',  # TODO name
            0,  # TODO narrative object ID TODO
            iso8601_to_epoch(moddate),  # Save date as an epoch
            owner,
            user_profile_map[owner]['user']['realname'],
        ]
    return (ws_infos, narr_infos)


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
        obj: dict = {}
        for (search2_key, search1_key) in _KEY_MAPPING.items():
            obj[search1_key] = source.get(search2_key)
        # The nested 'data' is all object-specific, so disclude all global keys
        obj['data'] = {key: source[key] for key in source if key not in _KEY_MAPPING}
        # Set defaults for required fields in objects/data
        # FIXME we need to actually fill these fields with real data every time
        obj['data']['creator'] = obj['data'].get('creator', '')
        obj['data']['shared_users'] = obj['data'].get('shared_users', [])
        obj['data']['timestamp'] = obj['data'].get('timestamp', 0)
        obj['data']['creation_date'] = obj['data'].get('creation_date', '')
        obj['data']['is_public'] = obj['data'].get('is_public', False)
        obj['data']['access_group'] = obj['data'].get('access_group', 0)
        obj['data']['obj_id'] = obj['data'].get('obj_id', 0)
        obj['data']['version'] = obj['data'].get('obj_id', 0)
        obj['data']['copied'] = obj['data'].get('copied')
        obj['data']['tags'] = obj['data'].get('tags', [])
        # Set some more top-level data manually that we use in the UI
        obj['key_props'] = obj['data']
        obj['guid'] = _get_guid_from_doc(result)
        obj['kbase_id'] = obj['guid'].strip('WS:')
        # Set to a string
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
        # Always set object_name as a string type
        obj['object_name'] = obj.get('object_name') or ''
        obj['type'] = obj.get('type') or ''
        object_data.append(obj)
    return object_data


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
