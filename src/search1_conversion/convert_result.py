from src.utils.config import config
from src.utils.formatting import iso8601_to_epoch_ms
from src.utils.user_profiles import get_user_profiles
from src.utils.workspace import get_workspace_info
from src.exceptions import NoAccessGroupError, NoUserProfileError

# TODO: The structure of the ES docs and of the API's result
# data should be documented in detail outside of this file, with a
# reference here.

# Mappings from search2 document fields to search1 fields.
_GLOBAL_DOC_KEY_MAPPING = {
    'obj_name': 'object_name',
    'access_group': 'workspace_id',
    'obj_id': 'object_id',
    'version': 'object_version',
    'obj_type_module': 'workspace_type_module',
    'obj_type_name': 'workspace_type_name',
    'obj_type_version': 'workspace_type_version',
    'timestamp': 'modified_at'
}

# These keys are copied over literally without renaming
# keys or transformation
_GLOBAL_DOC_KEY_COPYING = [
    'creator',
    'copied'
]

# These keys are copied from the result "hit", not "hit.doc" as
# above.
_GLOBAL_HIT_KEY_COPYING = [
    'id'
]

# These keys are to be neither mapped nor copied, but when copying the rest of the
# doc fields into the data field, should be excluded, or omitted.
_GLOBAL_DOC_KEY_EXCLUSION = [
    'is_public',
    'shared_users',
    'tags',
    'index_runner_ver'
]

# Similar to excluded fields, these fields are transformed and copied in code below
# (see the "# Transforms" comment) and should be ignored when copying into the data field.
_GLOBAL_DOC_KEY_TRANSFORMS = [
    'creation_date'
]


def search_objects(params: dict, results: dict, ctx: dict):
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
    _add_access_group_info(ret, results, ctx, post_processing)
    _add_objects_and_info(ret, results, ctx, post_processing)

    return ret


def search_types(_params, results, _ctx):
    """
    Convert Elasticsearch results into RPC results conforming to the
    "search_types" method.
    """
    # Convert the ES result format into the API format
    search_time = results['search_time']
    type_counts = results['aggregations']['type_count']['counts']
    type_to_count = {}  # type: dict

    for type_count in type_counts:
        key = type_count['key']
        count = type_count['count']
        type_to_count[key] = count
    return {
        'type_to_count': type_to_count,
        'search_time': int(search_time)
    }


def get_objects(params, results, ctx):
    """
    Convert Elasticsearch results into RPC results conforming to the spec for
    the "get_objects" method.
    """
    post_processing = _get_post_processing(params)
    ret = {
        'search_time': results['search_time'],
    }
    _add_access_group_info(ret, results, ctx, post_processing)
    _add_objects_and_info(ret, results, ctx, post_processing)
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


def _add_objects_and_info(ret: dict, search_results: dict, ctx: dict, post_processing: dict):
    """
    Populate the fields for `objects`.

    Args:
        ret: final method result object (mutated)
        search_results: return value from es_client.query.search
        ctx: RPC context object (contains auth token)
        post_processing: some query options pulled from the RPC method params
    """
    objects = _get_object_data_from_search_results(search_results, post_processing)
    ret['objects'] = objects


def _add_access_group_info(ret: dict, search_results: dict, ctx: dict, post_processing: dict):
    """
    Populate the fields for `access_group_narrative_info` and/or
    `access_groups_info` depending on keys from the `post_processing` field.
    This mutates the method result object (`ret`)

    Args:
        ret: final method result object (mutated)
        search_results: return value from es_client.query.search
        ctx: RPC context object (contains auth token)
        post_processing: some query options pulled from the RPC method params
    """
    fetch_narratives = post_processing.get('add_narrative_info') == 1
    fetch_ws_infos = post_processing.get('add_access_group_info') == 1
    if fetch_narratives or fetch_ws_infos:
        (ws_infos, narrative_infos) = _fetch_narrative_info(search_results, ctx)
        if fetch_narratives:
            ret['access_group_narrative_info'] = narrative_infos
        if fetch_ws_infos:
            ret['access_groups_info'] = ws_infos


def _fetch_narrative_info(es_result, ctx):
    """
    Returns a to mappings of workspaces, each keyed on the workspace id:
    - a subset of workspace info as returned by the workspace:
      (id, name, owner, save_date, max_objid, user_perm, global_perm,
       lockstat, metadata)
    - a subset of narrative info for workspaces which are narratives, a tuple
      of selected values:
      (narrative title, object id, workspace modification timestamp,
       owner username, owner realname)

    The reason for the duplication is historical, not intentional design.
    One day we will rectify this.

    (id, name, owner, save_date, max_objid, user_perm, global_perm, lockstat, metadata)
    """
    hit_docs = [hit['doc'] for hit in es_result['hits']]
    workspace_ids = set()
    ws_infos = {}
    owners = set()

    # Get workspace info for all unique workspaces in the search
    # results
    for hit_doc in hit_docs:
        if 'access_group' not in hit_doc:
            raise NoAccessGroupError()
        workspace_id = hit_doc['access_group']
        workspace_ids.add(workspace_id)

    if len(workspace_ids) == 0:
        return {}, {}

    for workspace_id in workspace_ids:
        workspace_info = get_workspace_info(workspace_id, ctx['auth'])
        if len(workspace_info) > 2:
            owners.add(workspace_info[2])
            ws_infos[str(workspace_id)] = workspace_info

    # Get profile for all owners in the search results
    owner_list = list(owners)
    user_profiles = get_user_profiles(owner_list, ctx['auth'])
    user_profile_map = {}
    for index, profile in enumerate(user_profiles):
        if profile is None:
            raise NoUserProfileError(owner_list[index])
        username = profile['user']['username']
        user_profile_map[username] = profile

    # Get all the source document objects for each narrative result
    narr_infos = {}
    for ws_info in ws_infos.values():
        [workspace_id, _, owner, moddate, _, _, _, _, ws_metadata] = ws_info
        user_profile = user_profile_map.get(owner)
        real_name = user_profile['user']['realname']
        if 'narrative' in ws_metadata:
            narr_infos[str(workspace_id)] = [
                ws_metadata.get('narrative_nice_name', ''),
                int(ws_metadata.get('narrative')),
                iso8601_to_epoch_ms(moddate),
                owner,
                real_name
            ]
    return ws_infos, narr_infos


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
    for hit in search_results['hits']:
        doc = hit['doc']
        obj: dict = {}

        # Copy fields from the "hit" to the result "object".
        for key in _GLOBAL_HIT_KEY_COPYING:
            obj[key] = hit.get(key)

        # Simple key mapping from the doc to the object.
        # The mapping transforms the raw keys from the ES result into
        # friendlier keys expected by the API.
        # Defined at top of file.
        global_doc_keys = []
        for (search2_key, search1_key) in _GLOBAL_DOC_KEY_MAPPING.items():
            global_doc_keys.append(search2_key)
            obj[search1_key] = doc.get(search2_key)

        #  Even simpler key mapping - no key substitution
        for key in _GLOBAL_DOC_KEY_COPYING:
            global_doc_keys.append(key)
            obj[key] = doc.get(key)

        # Transforms
        obj['created_at'] = iso8601_to_epoch_ms((doc['creation_date']))

        # The index name from the external pov is unqualified and
        # unversioned; it is equivalent to the index alias, and
        # symmetric with any parameters which limit searches by
        # index.
        # The form of object indexes is:
        # NAMESPACE.INDEXNAME_VERSION
        # (why different separators for prefix and suffix?)
        # e.g. search2.genome_2
        # We are interested in the INDEXNAME and VERSION,
        # although there is no need for clients to know the version
        # it may be useful for diagnostics.
        idx_pieces = hit['index'].split(config['suffix_delimiter'])
        idx_name = idx_pieces[0]

        # TODO: we should not default to 0, but rather raise an
        # error. All indexes involved should be namespaced.
        idx_ver = int(idx_pieces[1] or 0) if len(idx_pieces) == 2 else 0
        obj['index_name'] = idx_name
        obj['index_version'] = idx_ver

        # Funny Business
        # Always set object_name as a string type
        # TODO: how can this ever be missing? It is simply impossible, every
        # object has a name and a type.
        obj['object_name'] = obj.get('object_name') or ''
        obj['workspace_type_name'] = obj.get('workspace_type_name') or ''

        # The nested 'data' is all object-specific, so exclude all global keys
        # The indexed doc mixes global keys and index-specific ones.
        # The search1 api separated them, so this transformation respects that.
        obj_data = {key: doc[key] for key in doc if key not in global_doc_keys
                    and key not in _GLOBAL_DOC_KEY_EXCLUSION
                    and key not in _GLOBAL_DOC_KEY_TRANSFORMS}

        if post_processing.get('skip_data') != 1:
            obj['data'] = obj_data

        # Highlights are mappings of key to a formatted string
        # derived from the field with "hit" terms highlighted with
        # html.
        # These fields may be any field in the indexed doc, which
        # mixes global and index-specific fields.
        # We need to transform the keys, if the GLOBAL_KEY_MAPPING
        # so deems; otherwise we use the keys directly.
        # TODO: improvements needed here; not all search terms are highlighted
        # as a result of this transform, which results in a confusing message
        # on the front end.
        if post_processing.get('include_highlight') == 1:
            highlight = hit.get('highlight', {})
            transformed_highlight = {}
            for key, value in highlight.items():
                transformed_highlight[_GLOBAL_DOC_KEY_MAPPING.get(key, key)] = value
            obj['highlight'] = transformed_highlight

        object_data.append(obj)
    return object_data
