"""
Search objects on elasticsearch
"""
import json
import requests

from src.workspace_auth import ws_auth
from src.utils.config import init_config

_CONFIG = init_config()


def search_objects(params, headers):
    """
    Make a query on elasticsearch using the given index and options.

    Args:
        params - dict of parameters from the JSON RPC request to the server
            can contain:
                `query` options for elasticsearch
                `source` - array of field names to return in the "_source"
                `indexes` - array of index names (without any prefix)
                `only_public` - only show public workspace data
                `only_private` - only show private workspace data
                `size` - result length to return for pagination
                `from` - result offset for pagination
                `count` - take a count of the query, instead of listing results ? TODO

    ES 5.5 search query documentation:
    https://www.elastic.co/guide/en/elasticsearch/reference/5.5/search-request-body.html
    """
    user_query = params.get('query', {})
    authorized_ws_ids = []  # type: list
    if not params.get('public_only') and headers.get('Authorization'):
        # Fetch the workspace IDs that the user can read
        # Used for simple access control
        authorized_ws_ids = ws_auth(headers['Authorization'])
    # Lower-case and prefix every provided index name
    if params.get('indexes'):
        index_names = [
            _CONFIG['index_prefix'] + '.' + name.lower()
            for name in params['indexes']
        ]
        index_name_str = ','.join(index_names)
    else:
        index_name_str = _CONFIG['index_prefix'] + '.*'
    # We insert the user's query as a "must" entry
    query = {'bool': {'must': user_query}}
    # Our access control query is then inserted under a "filter" depending on options:
    if params.get('public_only'):
        # Public workspaces only; most efficient
        query['bool']['filter'] = {'term': {'is_public': True}}
    elif params.get('private_only'):
        # Private workspaces only
        query['bool']['filter'] = {
            'bool': {
                'must': [
                    {'term': {'is_public': False}},
                    {'terms': {'access_group': authorized_ws_ids}}
                ]
            }
        }
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
    # url += '/_count' if params.get('count') else '/_search'
    options = {
        'query': query,
        'terminate_after': 10000,  # type: ignore
        'size': 0 if params.get('count') else params.get('size', 10),
        'from': params.get('from', 0),
        'timeout': '3m'  # type: ignore
    }
    # User-supplied aggregations
    if params.get('aggs'):
        options['aggs'] = params['aggs']
    # User-supplied sorting rules
    if params.get('sort'):
        options['sort'] = params['sort']
    # User-supplied source filters
    if params.get('source'):
        options['_source'] = params.get('source')
    print('options!', options)
    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, data=json.dumps(options), headers=headers)
    if not resp.ok:
        raise RuntimeError(resp.text)
    return resp.json()
