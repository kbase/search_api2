"""
Search objects on elasticsearch
"""
import re
import json
import requests
import logging

from src.workspace_auth import ws_auth
from src.utils.config import init_config

_CONFIG = init_config()

logger = logging.getLogger('searchapi2')


def search_objects(params, headers):
    """
    Make a query on elasticsearch using the given index and options.

    See method_schemas.json for a definition of the params

    ES 5.5 search query documentation:
    https://www.elastic.co/guide/en/elasticsearch/reference/5.5/search-request-body.html
    """
    user_query = params.get('query')
    authorized_ws_ids = []  # type: list
    if not params.get('public_only') and headers.get('Authorization'):
        # Fetch the workspace IDs that the user can read
        # Used for simple access control
        authorized_ws_ids = ws_auth(headers['Authorization'])
    # Get the index name(s) to include and exclude (used in the URL below)
    index_name_str = _construct_index_name(params)
    # We insert the user's query as a "must" entry
    query = {'bool': {}}  # type: dict
    if user_query:
        query['bool']['must'] = user_query
    # Our access control query is then inserted under a "filter" depending on options:
    if params.get('public_only'):
        # Public workspaces only; most efficient
        query['bool']['filter'] = {'term': {'is_public': True}}
    elif params.get('private_only'):
        # Private workspaces only
        query['bool']['filter'] = [
            {'term': {'is_public': False}},
            {'terms': {'access_group': authorized_ws_ids}}
        ]
    else:
        # Find all documents, whether private or public
        query['bool']['filter'] = {
            'bool': {
                'should': [
                    {'term': {'is_public': True}},
                    {'terms': {'access_group': authorized_ws_ids}}
                ]
            }
        }
    # Make a query request to elasticsearch
    url = _CONFIG['elasticsearch_url'] + '/' + index_name_str + '/_search'
    options = {
        'query': query,
        'size': 0 if params.get('count') else params.get('size', 10),
        'from': params.get('from', 0),
        'timeout': '3m'  # type: ignore
    }
    if not params.get('count') and params.get('size', 10) > 0:
        options['terminate_after'] = 10000  # type: ignore
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
        options['highlight'] = {'fields': params['highlight']}
    if params.get('track_total_hits'):
        options['track_total_hits'] = params.get('track_total_hits')
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, data=json.dumps(options), headers=headers)
    if not resp.ok:
        # Unexpected elasticsearch error
        raise RuntimeError(resp.text)
    resp_json = resp.json()
    result = _handle_response(resp_json)
    return result


def _handle_response(resp_json):
    """
    Translation layer between the Elasticsearch response and our API's response.
    When the Elasticsearch API changes, we need to update this function.
    """
    prefix = _CONFIG['index_prefix']
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
    prefix = _CONFIG['index_prefix']
    # index_name_str = prefix + "."
    index_name_str = prefix + ".default_search"
    if params.get('indexes'):
        index_names = [
            prefix + '.' + name.lower()
            for name in params['indexes']
        ]
        # Replace the index_name_str with all explicitly included index names
        index_name_str = ','.join(index_names)
    # Append any index name exclusions, if necessary
    if params.get('exclude_indexes'):
        exclusions = params['exclude_indexes']
        exclusions_str = ','.join('-' + prefix + '.' + name for name in exclusions)
        index_name_str += ',' + exclusions_str
    return index_name_str
