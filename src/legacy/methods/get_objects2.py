from src.search_objects import search_objects
import src.legacy.common as common


def get_objects2(params, auth):
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

    doc_ids = common.refs_to_doc_ids(params['refs'])

    params = {
        'query': {
            'terms': {
                '_id': doc_ids
            }
        }
    }

    search_results = search_objects(params, {
        'Authorization': auth
    })

    objects = common.get_object_data_from_search_results(search_results, post_processing)
    workspaces = common.fetch_workspaces_info(search_results, auth)
    return {
        'search_time': search_results['search_time'],
        'objects': objects,
        'workspaces': workspaces
    }
