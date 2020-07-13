"""
JSON-RPC 2.0 service for the Search2 API
"""
import jsonrpcbase
import re
import requests
import time

from src.es_client import search
from src.utils.config import config
from src.utils.logger import logger

service = jsonrpcbase.JSONRPCService(
    info={
        'title': 'Search API',
        'description': 'Search API layer in front of Elasticsearch for KBase',
        'version': config['app_version'],
    },
    schema='rpc-schema.yaml',
    development=config['dev'],
)


def show_indexes(params, meta):
    """List all index names for our prefix"""
    prefix = config['index_prefix']
    resp = requests.get(
        config['elasticsearch_url'] + '/_cat/indices/' + prefix + '*?format=json',
        headers={'Content-Type': 'application/json'},
    )
    if not resp.ok:
        # TODO better error class
        raise RuntimeError(f'Elasticsearch error:\n{resp.text}')
    resp_json = resp.json()
    result = []
    # Drop the prefixes
    for each in resp_json:
        regex = f"^{config['index_prefix']}."
        name = re.sub(regex, '', each['index'])
        idx = {
            'name': name,
            'count': int(each['docs.count'])
        }
        result.append(idx)
    return result


def show_config(params, meta):
    """
    Display publicly readable configuration settings for this server.
    Be sure to add new entries here explicitly so that nothing is shown unintentionally.
    """
    exposed_keys = ['dev', 'elasticsearch_url', 'workspace_url', 'index_prefix',
                    'global', 'workers', 'user_profile_url']
    return {key: config[key] for key in exposed_keys}


def search_objects(params, meta):
    start = time.time()
    result = search(params, meta)
    logger.debug(f"Finished 'search_objects' method in {time.time() - start}s")
    return result


service.add(show_indexes)
service.add(show_config)
service.add(search_objects)
