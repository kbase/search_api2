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

import time
import os
from jsonrpc11base import JSONRPCService
from jsonrpc11base.service_description import ServiceDescription
from jsonrpc11base.errors import ServerError
from src.exceptions import AuthError
from src.es_client import search
from src.search1_conversion import convert_params, convert_result
from src.utils.logger import logger

description = ServiceDescription(
    'Example Database Service',
    'https://github.com/kbase/kbase-jsonrpc11base/examples/database',
    summary='An example JSON-RPC 1.1 service implementing a simple database',
    version='1.0'
)


class AuthorizationServerError(ServerError):
    code = -32001
    message = 'Auth error'

    def __init__(self, message):
        self.error = {
            'message': message
        }


SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'data/schema')

service = JSONRPCService(
    description=description,
    schema_dir=None,
    validate_result=False
)


def search_handle_errors(query, meta):
    try:
        return search(query, meta)
    except AuthError as ae:
        raise AuthorizationServerError(ae.message)


def get_objects(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.get_objects(params)
    search_result = search_handle_errors(query, meta)
    result = convert_result.get_objects(params, search_result, meta)
    logger.debug(f'Finished get_objects in {time.time() - start}s')
    # KBase convention is to return result in a list
    return [result]


def search_objects(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.search_objects(params)
    search_result = search_handle_errors(query, meta)
    result = convert_result.search_objects(params, search_result, meta)
    logger.debug(f'Finished search_objects in {time.time() - start}s')
    # KBase convention is to return result in a list
    return [result]


def search_types(params, meta):
    # KBase convention is to wrap params in an array
    if isinstance(params, list) and len(params) == 1:
        params = params[0]
    start = time.time()
    query = convert_params.search_types(params)
    search_result = search_handle_errors(query, meta)
    result = convert_result.search_types(params, search_result, meta)
    logger.debug(f'Finished search_types in {time.time() - start}s')
    # KBase convention is to return result in a list
    return [result]


service.add(get_objects, name="KBaseSearchEngine.get_objects")
service.add(search_objects, name="KBaseSearchEngine.search_objects")
service.add(search_types, name="KBaseSearchEngine.search_types")
