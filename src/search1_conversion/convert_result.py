import re
from src.utils.config import config
from src.utils.formatting import iso8601_to_epoch
from src.utils.user_profiles import get_user_profiles
from src.utils.workspace import get_workspace_info

# Mappings from search2 document fields to search1 fields:
_KEY_MAPPING = {
    'obj_name': 'object_name',
    'access_group': 'access_group',
    'obj_id': 'obj_id',
    'version': 'version',
    'timestamp': 'timestamp',
    'obj_type_name': 'type',
    'creator': 'creator'
}


def search_objects(params: dict, results: dict, meta: dict):
    """
    Convert Elasticsearch results into the RPC results conforming to the
    "search_objects" method
    """
    post_processing = _get_post_processing(params)
    objects = _get_object_data_from_search_results(results, post_processing)
    ret = {
        'pagination': params.get('pagination', {}),
        'sorting_rules': params.get('sorting_rules', []),
        'total': results['count'],
        'search_time': results['search_time'],
        'objects': objects,
    }
    _add_access_group_info(ret, results, meta, post_processing)
    _add_objects_and_info(ret, results, meta, post_processing)
    return ret


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
    return {
        'type_to_count': counts_dict,
        'search_time': int(search_time)
    }


def get_objects(params, results, meta):
    """
    Convert Elasticsearch results into RPC results conforming to the spec for
    the "get_objects" method.
    """
    post_processing = _get_post_processing(params)
    ret = {
        'search_time': results['search_time'],
    }
    _add_access_group_info(ret, results, meta, post_processing)
    _add_objects_and_info(ret, results, meta, post_processing)
    return ret


def _get_post_processing(params: dict) -> dict:
    """
    Extract and set defaults for the post processing options
    """
    pp = params.get('post_processing', {})
    # ids_only - shortcut to mark both skips as true and include_highlight as false.
    if pp.get('ids_only') == 1:
        pp['include_highlight'] = 0
        pp['skip_info'] = 1
        pp['skip_data'] = 1
    return pp


def _add_objects_and_info(ret: dict, search_results: dict, meta: dict, post_processing: dict):
    """
    Populate the fields for `objects`.

    Args:
        ret: final method result object (mutated)
        search_results: return value from es_client.query.search
        meta: RPC meta object (contains auth token)
        post_processing: some query options pulled from the RPC method params
    """
    objects = _get_object_data_from_search_results(search_results, post_processing)
    ret['objects'] = objects


def _add_access_group_info(ret: dict, search_results: dict, meta: dict, post_processing: dict):
    """
    Populate the fields for `access_group_narrative_info` and/or
    `access_groups_info` depending on keys from the `post_processing` field.
    This mutates the method result object (`ret`)

    Args:
        ret: final method result object (mutated)
        search_results: return value from es_client.query.search
        meta: RPC meta object (contains auth token)
        post_processing: some query options pulled from the RPC method params
    """
    fetch_narratives = post_processing.get('add_narrative_info') == 1
    fetch_ws_infos = post_processing.get('add_access_group_info') == 1
    if fetch_narratives or fetch_ws_infos:
        (ws_infos, narrative_infos) = _fetch_narrative_info(search_results, meta)
        if fetch_narratives:
            ret['access_group_narrative_info'] = narrative_infos
        if fetch_ws_infos:
            ret['access_groups_info'] = ws_infos


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
    workspace_ids = set()
    ws_infos = {}
    owners = set()

    # Get workspace info for all unique workspaces in the search
    # results
    for hit_doc in hit_docs:
        if 'access_group' not in hit_doc:
            continue
        workspace_id = hit_doc['access_group']
        workspace_ids.add(workspace_id)

    for workspace_id in workspace_ids:
        workspace_info = get_workspace_info(workspace_id, meta['auth'])
        if len(workspace_info) > 2:
            owners.add(workspace_info[2])
            ws_infos[str(workspace_id)] = workspace_info

    if len(workspace_ids) == 0:
        return ({}, {})

    # Get profile for all owners in the search results
    user_profiles = get_user_profiles(list(owners), meta['auth'])
    user_profile_map = {}
    for profile in user_profiles:
        if profile is not None:
            username = profile['user']['username']
            user_profile_map[username] = profile

    # user_profile_map = {profile['user']['username']: profile for profile in user_profiles}
    narrative_index_name = config['global']['ws_type_to_indexes']['KBaseNarrative.Narrative']
    # TODO move this code into es_client.fetch_narratives
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

    # Get all the source document objects for each narrative result
    narr_infos = {}
    for ws_info in ws_infos.values():
        [workspace_id, workspace_name, owner, moddate,
         max_objid, user_permission, global_permission,
         lockstat, ws_metadata] = ws_info
        user_profile = user_profile_map.get(owner)
        if user_profile is not None:
            real_name = user_profile['user']['realname']
        else:
            # default to real name if the user profile is absent.
            real_name = owner
        if 'narrative' in ws_metadata:
            narr_infos[str(workspace_id)] = [
                ws_metadata.get('narrative_nice_name', ''),
                int(ws_metadata.get('narrative')),
                iso8601_to_epoch(moddate) * 1000,
                owner,
                real_name
            ]
    return (ws_infos, narr_infos)


def _get_object_data_from_search_results(search_results, post_processing):
    """
    Construct a list of ObjectData (see the type def in the module docstring at top).
    Uses the post_processing options (see the type def for PostProcessing at top).
    We translate fields from our current ES indexes to naming conventions used by the legacy API/UI.
    """
    # TODO post_processing/skip_info,skip_keys,skip_data -- look at results in current api
    # TODO post_processing/ids_only -- look at results in current api
    object_data = []  # type: list
    # Keys found in every ws object
    for result in search_results['hits']:
        source = result['doc']
        obj: dict = {}
        for (search2_key, search1_key) in _KEY_MAPPING.items():
            obj[search1_key] = source.get(search2_key)
        # The nested 'data' is all object-specific, so exclude all global keys
        obj_data = {key: source[key] for key in source if key not in _KEY_MAPPING}
        if post_processing.get('skip_data') != 1:
            obj['data'] = obj_data
        obj['guid'] = _get_guid_from_doc(result)
        obj['kbase_id'] = obj['guid'].strip('WS:')
        idx_pieces = result['index'].split(config['prefix_delimiter'])
        idx_name = idx_pieces[0]
        idx_ver = int(idx_pieces[1] or 0) if len(idx_pieces) == 2 else 0

        obj['index_name'] = idx_name
        obj['type_ver'] = idx_ver
        # For the UI, make the type field "GenomeFeature" instead of "Genome".
        if 'genome_feature_type' in source:
            obj['type'] = 'GenomeFeature'
        # Set defaults for required fields in objects/data
        # Set some more top-level data manually that we use in the UI
        if post_processing.get('include_highlight') == 1:
            highlight = result.get('highlight', {})
            transformed_highlight = {}
            for key, value in highlight.items():
                transformed_highlight[_KEY_MAPPING.get(key, key)] = value
            obj['highlight'] = transformed_highlight
        # Always set object_name as a string type
        obj['object_name'] = obj.get('object_name') or ''
        obj['type'] = obj.get('type') or ''
        object_data.append(obj)
    return object_data


def _get_guid_from_doc(doc):
    """
    Convert from our guid format 'WS::1:2:3' into the legacy format 'WS:1/2/3'
    """
    # TODO this only works on the WS namespace should take into account the
    #      namespace name
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
