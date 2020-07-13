"""
JSON-RPC 2.0 service for the legacy API

All methods follow this workflow:
    - convert RPC params into Elasticsearch query
    - Make Elasticsearch request
    - Convert result into RPC result format according to spec

These methods are a composition of:
    - search1_conversion.convert_params
    - es_client.search
    - search1_conversion.convert_result
"""
import jsonrpcbase
import time

from src.es_client import search
from src.search1_conversion import convert_params, convert_result
from src.utils.config import config
from src.utils.logger import logger

service = jsonrpcbase.JSONRPCService(
    info={
        'title': 'Search API (legacy endpoints)',
        'description': 'Search endpoints for the legacy API',
        'version': config['app_version'],
    },
    schema='legacy-schema.yaml',
    development=config['dev'],
)


def get_objects(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.get_objects(params)
    result = convert_result.get_objects(params, search(query, meta), meta)
    logger.debug(f'Finished get_objects in {time.time() - start}s')
    # KBase convention is to return result in a singleton list
    return [result]


def search_objects(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.search_objects(params)
    result = convert_result.search_objects(params, search(query, meta), meta)
    logger.debug(f'Finished search_objects in {time.time() - start}s')
    # KBase convention is to return result in a singleton list
    return [result]


def search_types(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.search_types(params)
    result = convert_result.search_types(params, search(query, meta), meta)
    logger.debug(f'Finished search_types in {time.time() - start}s')
    # KBase convention is to return result in a singleton list
    return [result]


service.add(get_objects, name="KBaseSearchEngine.get_objects")
service.add(search_objects, name="KBaseSearchEngine.search_objects")
service.add(search_types, name="KBaseSearchEngine.search_types")
