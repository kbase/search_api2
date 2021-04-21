"""
JSON-RPC 1.1 service for the legacy API

All methods follow this workflow:
    - convert RPC params into Elasticsearch query
    - Make Elasticsearch request
    - Convert result into RPC result format according to spec

These methods are a composition of:
    - search1_conversion.convert_params
    - es_client.search
    - search1_conversion.convert_result

Note that the methods implement KBase's convention for JSON-RPC 1.1,
in which the request `params` are an array of one element, usually containing
an object, each property of which is considered a `param`, and in which the
results are also wrapped in an array of one element.
"""

import time
import os
from jsonrpc11base import JSONRPCService
from jsonrpc11base.service_description import ServiceDescription
from src.es_client.query import search
from src.search1_conversion import convert_params, convert_result
from src.utils.logger import logger
from src.search1_rpc.errors import trap_error

# A JSON-RPC 1.1 service description
description = ServiceDescription(
    'The KBase Legacy Search API',
    'https://github.com/kbase/search_api2/src/search1_rpc/schemas',
    summary='This is the legacy search interface to the KBase search  service',
    version='1.0'
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

service = JSONRPCService(
    description=description,
    schema_dir=SCHEMA_DIR,
    validate_params=True,
    validate_result=True
)


def get_objects(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.get_objects(params)
    search_result = trap_error(lambda: search(query, meta))
    result = convert_result.get_objects(params, search_result, meta)
    logger.debug(f'Finished get_objects in {time.time() - start}s')
    return [result]


def search_objects(params, meta):
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.search_objects(params)
    search_result = trap_error(lambda: search(query, meta))
    result = convert_result.search_objects(params, search_result, meta)
    logger.debug(f'Finished search_objects in {time.time() - start}s')
    return [result]


def search_types(params, meta):
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.search_types(params)
    search_result = trap_error(lambda: search(query, meta))
    result = convert_result.search_types(search_result)
    logger.debug(f'Finished search_types in {time.time() - start}s')
    return [result]


service.add(get_objects, name="KBaseSearchEngine.get_objects")
service.add(search_objects, name="KBaseSearchEngine.search_objects")
service.add(search_types, name="KBaseSearchEngine.search_types")
