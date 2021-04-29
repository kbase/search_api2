"""
Search objects on elasticsearch
"""
import re
import json
import requests

from src.utils.logger import logger
from src.utils.workspace import ws_auth
from src.utils.config import config
from src.utils.obj_utils import get_path
from src.exceptions import UnknownIndex, ElasticsearchError


def search(params, meta):
    """
    Make a query on elasticsearch using the given index and options.

    See rpc-schema.yaml for a definition of the params

    ES 7 search query documentation:
    https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
    """

    # The query object, which we build up in steps below
    query = {'bool': {}}  # type: dict

    # Fetch the workspace IDs that the user can read.
    # Used for access control and also to ensure that workspaces which are
    # inaccessible, but have not yet been updated in search, are still filtered out.
    authorized_ws_ids = ws_auth(
        meta['auth'],
        params.get('only_public', False),
        params.get('only_private', False))

    query['bool']['filter'] = [
        {'terms': {'access_group': authorized_ws_ids}}
    ]

    # We insert the user's query as a "must" entry
    user_query = params.get('query')
    if user_query:
        query['bool']['must'] = user_query

    # Get the index name(s) to include and exclude (used in the URL below)
    index_name_str = _construct_index_name(params)

    # Make a query request to elasticsearch
    url = config['elasticsearch_url'] + '/' + index_name_str + '/_search'

    # TODO: address the performance settings below:
    # - 3m for timeout is seems excessive, and many other elements of the
    #   search process may have 1m timeouts; perhaps default to a lower limit, and
    #   allow a parameter to set the timeout to an arbitrary value
    # - the "allow_expensive_queries" setting has been disabled, why?
    options = {
        'query': query,
        'size': 0 if params.get('count') else params.get('size', 10),
        'from': params.get('from', 0),
        'timeout': '3m',
        # Disallow expensive queries, such as joins, to prevent any denial of service
        # 'search': {'allow_expensive_queries': False},
    }

    if not params.get('count') and params.get('size', 10) > 0 and not params.get('track_total_hits'):
        options['terminate_after'] = 10000

    # User-supplied aggregations
    if params.get('aggs'):
        options['aggs'] = params['aggs']

    # User-supplied sorting rules
    if params.get('sort'):
        options['sort'] = params['sort']

    # User-supplied source filters
    if params.get('source'):
        options['_source'] = params.get('source')

    # Search results highlighting
    if params.get('highlight'):
        options['highlight'] = params['highlight']

    if params.get('track_total_hits'):
        options['track_total_hits'] = params.get('track_total_hits')

    headers = {'Content-Type': 'application/json'}

    # Allows index exclusion; otherwise there is an error
    params = {'allow_no_indices': 'true'}

    resp = requests.post(url, data=json.dumps(options), params=params, headers=headers)

    if not resp.ok:
        _handle_es_err(resp)

    resp_json = resp.json()
    return _handle_response(resp_json)


def _handle_es_err(resp):
    """Handle a non-2xx response from Elasticsearch."""
    logger.error(f"Elasticsearch response error:\n{resp.text}")
    try:
        resp_json = resp.json()
    except Exception:
        raise ElasticsearchError(resp.text)
    err_type = get_path(resp_json, ['error', 'root_cause', 0, 'type'])
    err_reason = get_path(resp_json, ['error', 'reason'])
    if err_type is None:
        raise ElasticsearchError(resp.text)
    if err_type == 'index_not_found_exception':
        raise UnknownIndex(err_reason)
    raise ElasticsearchError(err_reason)


def _handle_response(resp_json):
    """
    Translation layer between the Elasticsearch response and our API's response.
    When the Elasticsearch API changes, we need to update this function.
    """
    prefix = config['index_prefix']
    hits = []
    for hit in resp_json['hits']['hits']:
        # Display the index name without prefix
        index_name = re.sub(f"^{prefix}.", "", hit['_index'])
        doc = {
            'index': index_name,
            'id': hit['_id'],
            'doc': hit['_source'],
        }
        if hit.get('highlight'):
            doc['highlight'] = hit['highlight']
        hits.append(doc)
    resp_aggs = resp_json.get('aggregations', {})
    aggs = {}  # type: dict
    for (agg_key, resp_agg) in resp_aggs.items():
        counts = []
        for bucket in resp_agg['buckets']:
            count = {
                'key': bucket['key'],
                'count': bucket['doc_count']
            }
            counts.append(count)
        aggs[agg_key] = {
            'count_err_upper_bound': resp_agg.get('doc_count_error_upper_bound', 0),
            'count_other_docs': resp_agg.get('sum_other_doc_count'),
            'counts': counts
        }
    result = {
        'count': resp_json['hits']['total']['value'],
        'hits': hits,
        'search_time': resp_json['took'],
        'aggregations': aggs
    }
    return result


def _construct_index_name(params):
    """
    Given the search_objects params, construct the index name for use in the
    URL of the query.
    See the docs about how this works:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/multi-index.html
    """
    prefix = config['index_prefix']
    delim = config['prefix_delimiter']
    index_name_str = prefix + delim + "default_search"
    if params.get('indexes'):
        index_names = [
            prefix + delim + name.lower()
            for name in params['indexes']
        ]
        # Replace the index_name_str with all explicitly included index names
        index_name_str = ','.join(index_names)
    # FIXME could not get `-indexname` in the url to work at all
    # Append any index name exclusions, if necessary
    # if params.get('exclude_indexes'):
    #     exclusions = params['exclude_indexes']
    #     # FIXME I could not get exclusions (prefixed with minus sign) to work
    #     exclusions_str = ','.join('-' + prefix + '*' + name for name in exclusions)
    #     index_name_str += ',' + exclusions_str
    return index_name_str
