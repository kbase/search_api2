from src.utils.config import init_config
import src.legacy.common as common
from src.search_objects import search_objects

_CONFIG = init_config()


def search_types2(params, auth):
    """
    Search for the number of objects of each type, matching constraints.
    params:
        match_filter
            search_term
            object_name
            timestamp
        access_filter
            with_private - boolean - include private objects
            with_public - boolean - include public objects
            with_all_history - ignored
    output:
        types - dict where keys are type names and vals are counts
        search_time - int - total time performing search
    This method constructs the same search parameters as `search_objects`, but
    aggregates results based on `obj_type_name`.
    """
    search_params = common.get_search_params2(params)

    # Create the aggregation clause using a 'terms aggregation'
    search_params['aggs'] = {
        'type_count': {
            'terms': {'field': 'obj_type_name'}
        }
    }
    search_params['size'] = 0
    search_results = search_objects(search_params, {
        'Authorization': auth
    })
    # Now we need to convert the ES result format into the API format
    search_time = search_results['search_time']
    buckets = search_results['aggregations']['type_count']['counts']
    counts_dict = {}  # type: dict
    for count_obj in buckets:
        counts_dict[count_obj['key']] = counts_dict.get(count_obj['key'], 0)
        counts_dict[count_obj['key']] += count_obj['count']
    return {
        'types': counts_dict,
        'search_time': int(search_time)
    }
