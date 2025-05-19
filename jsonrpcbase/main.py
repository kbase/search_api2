"""
Simple JSON-RPC service without transport layer

See README.md for details

Uses Google Style Python docstrings:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
"""
import json
import jsonschema
import logging

from typing import Callable, Optional, List, Union

import jsonrpcbase.exceptions as exceptions
import jsonrpcbase.types as types
import jsonrpcbase.utils as utils

# Reference: https://www.jsonrpc.org/specification
REQUEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JSON-RPC Request Schema",
    "description": "JSON-Schema that validates a JSON-RPC 2.0 request body (non-batch requests)",
    "type": "object",
    "additionalProperties": False,
    "required": ["jsonrpc", "method"],
    "properties": {
        "jsonrpc": {
            "const": "2.0"
        },
        "method": {
            "type": "string",
            "minLength": 1,
        },
        "id": {
            "type": ["integer", "string"]
        },
        "params": {
            "anyOf": [{"type": "object"}, {"type": "array"}]
        }
    }
}

# Reference: https://www.jsonrpc.org/specification#error_object
RPC_ERRORS = {
    # Invalid JSON was received. An error occurred on the server while parsing the JSON text.
    -32700: 'Parse error',
    # The JSON sent is not a valid Request object.
    -32600: 'Invalid Request',
    # The method does not exist / is not available.
    -32601: 'Method not found',
    # Invalid method parameter(s).
    -32602: 'Invalid params',
    # Internal JSON-RPC error.
    -32603: 'Internal error',
    # Reserved for implementation-defined server-errors.
    -32000: 'Server error',
}

log = logging.getLogger(__name__)


class JSONRPCService(object):
    """
    The JSONRPCService class is a JSON-RPC
    """

    # JSON-Schema for the service
    schema: dict
    # Flag for development mode (validate result schemas)
    development: bool
    # Mapping of method name to function handler
    method_data: types.MethodData
    # Service name, description, version, etc
    info: types.ServiceInfo

    def __init__(self,
                 info: Union[str, dict],
                 schema: Optional[Union[str, dict]] = None,
                 development: bool = False):
        """
        Initialize a new JSONRPCService object.

        Args:
            schema: JSON-Schema dict or path to a YAML or JSON file.
            development: Flag if we are in development mode. Dev mode checks
                all result schemas.
            info: service name, description, and version.
        """
        # Initialize service schema
        self.schema = utils.load_schema(schema)
        # A mapping of method name to python function and json-schema
        self.method_data = {
            'rpc.discover': types.Method(method=self._handle_discover)
        }
        self.development = development
        self.info = utils.load_service_info(info)

    def add(self, func: Callable, name: Optional[str] = None):
        """
        Adds a new method to the jsonrpc service. If name argument is not
        given, function's own name will be used.

        Example:
            service.add(myfunc, name='my_function')

        Args:
            func: required python function handler to call for this method
            name: optional name of the method (defaults to the function's name)
            schema: optional JSON-Schema for parameter validation
        """
        fname = name if name else func.__name__
        if fname in self.method_data:
            msg = f"Duplicate method name for JSON-RPC service: '{fname}'"
            raise exceptions.DuplicateMethodName(msg)
        self.method_data[fname] = types.Method(method=func)

    def call(self, jsondata: str, metadata=None) -> str:
        """
        Calls jsonrpc service's method and returns its return value in a JSON
        string or None if there is none.

        Args:
           jsondata: JSON-RPC 2.0 request body (raw string)
           metadata: any additional object to pass along to the handler function as the second arg

        Returns:
            The JSON-RPC 2.0 response as a raw JSON string.
            Will not throw an exception.
        """
        try:
            request_data = json.loads(jsondata)
        except ValueError as err:
            resp = self._err_response(-32700, err_data={'details': str(err)}, always_respond=True)
            return json.dumps(resp)
        result = self.call_py(request_data, metadata)
        if result is not None:
            return json.dumps(result)

    def call_py(self, req_data: types.MethodRequest, metadata=None) -> types.MethodResult:
        """
        Call a method in the service and return the RPC response. This behaves
        the same as call() except that the request and response are python
        objects instead of JSON strings.

        Args:
            req_data: JSON-RPC 2.0 request payload as a python object
            metadata: Any optional additional data to send to the handler function

        Returns:
            The JSON-RPC 2.0 response as a python object.
            Returns None if the request is a notification.
            Will not throw an exception.
        """
        if isinstance(req_data, list):
            if len(req_data) == 0:
                err_data = {'details': 'Batch request array is empty'}
                return self._err_response(-32600, err_data=err_data, always_respond=True)
            return self._call_batch(req_data, metadata)
        return self._call_single(req_data, metadata)

    def _call_single(self, req_data: dict, metadata) -> dict:
        """
        Make a single method call (used in call_py() and _call_batch())
        Args:
            req_data: JSON-RPC 2.0 parsed request parameter data
            metadata: Any user-supplied additional data to be passed to the method handler
        Returns:
            JSON-RPC 2.0 result data.
        Raises:
            jsonschema.ValidationError
            exceptions.InvalidServerErrorCode
        """
        # Validate the request body using a json-schema
        try:
            jsonschema.validate(req_data, REQUEST_SCHEMA)
        except jsonschema.exceptions.ValidationError as err:
            log.exception(f'Invalid JSON-RPC request for {req_data}: {err}')
            data = {
                'details': err.message,
            }
            return self._err_response(-32600, req_data, err_data=data, always_respond=True)
        # Handle unknown method error
        if req_data['method'] not in self.method_data:
            # Missing method
            meths = list(self.method_data.keys())
            err_data = {'available_methods': meths}
            return self._err_response(-32601, req_data, err_data=err_data)
        method = self.method_data[req_data['method']].method
        params = req_data.get('params')
        (params_schema, result_schema) = utils.get_method_schemas(self.schema, req_data['method'])
        # Validate the parameters with the json-schema, if present
        if (req_data['method'] in self.schema['definitions']['methods']
                and params_schema is None
                and params is not None):
            # If there is an entry for the method, but no params schema, then params must be absent
            err_data = {'details': "Parameters not allowed"}
            return self._err_response(-32602, req_data, err_data)
        elif params_schema is not None:
            # Allow referencing of definitions from the service schema
            params_schema['definitions'] = self.schema['definitions']
            try:
                jsonschema.validate(params, params_schema)
            except jsonschema.exceptions.ValidationError as err:
                # Invalid params error response
                err_data = {'details': err.message, 'path': list(err.path)}
                return self._err_response(-32602, req_data, err_data)
        try:
            result = method(params, metadata)
        except Exception as err:
            # Exception was raised inside the method.
            log.exception(f"Method {req_data['method']} threw an exception: {err}")
            err_data = {'method': req_data['method']}
            if hasattr(err, 'message'):
                err_data['details'] = err.message
            code = -32000  # Server error
            if hasattr(err, 'jsonrpc_code'):
                code = err.jsonrpc_code
                if code > -32000 or code < -32099:
                    msg = (
                        f"Invalid server error code '{code}'; "
                        "must be in the range -32000 to -32099."
                    )
                    raise exceptions.InvalidServerErrorCode(msg)
            return self._err_response(code, req_data, err_data)
        # Validate the result in development mode, if a result schema was supplied
        if self.development and result_schema:
            result_schema['definitions'] = self.schema['definitions']
            # Raises jsonschema.ValidationError
            jsonschema.validate(result, result_schema)
        _id = utils.response_id(req_data)
        if type(_id) in (str, int):
            # Return the result in JSON-RPC 2.0 response format
            return {
                'id': _id,
                'jsonrpc': '2.0',
                'result': result,
            }
        else:
            # Notification request; no results
            return None

    def _call_batch(self, req_data: List[dict], metadata) -> Optional[List[dict]]:
        """
        Make many method calls (used in call_py())
        """
        results = []
        for req in req_data:
            resp = self._call_single(req, metadata)
            # According to the spec, notification requests do not go in the result array
            if resp is not None:
                results.append(resp)
        # Equivalent to something like `return results or None`, but let's be explicit:
        if len(results) == 0:
            # Every request was a notification
            return None
        else:
            return results

    def _err_response(self,
                      code: int,
                      req_data: Optional[dict] = None,
                      err_data: Optional[dict] = None,
                      always_respond: bool = False) -> dict:
        """
        Return a JSON-RPC 2.0 error response. The 'message' field is
        autopopulated from the code based on values from the spec.

        Args:
            code: JSON-RPC 2.0 error code
            req_data: Request data as a python object
            err_data: Optional 'data' field for the error response
            always_respond: Even if there was no ID in the request, send a response
        Returns:
            JSON-RPC 2.0 error response as a python dict.

        ID behavior:
        - If req_data is None and always_respond is True, then a response is
          returned with 'id' of null
        - If req_data is None and always_respond is False, then None is returned
        - If req_data has a valid ID, then that is returned in the response
        - If req_data does not have a valid ID and always_respond is True,
          then 'id' is null in the response
        - If req_data does not have a valid ID and always_response is False, then None is returned
        """
        _id = utils.response_id(req_data) if req_data else None
        if _id is None and not always_respond:
            # Do not return error responses for notifications
            return None
        resp = {
            'jsonrpc': '2.0',
            'id': _id,
            'error': {
                'code': code,
                'message': RPC_ERRORS.get(code, 'Server error'),
            }
        }
        if err_data:
            resp['error']['data'] = err_data
        return resp

    def _handle_discover(self, params, meta) -> dict:
        """
        Built-in method handler that shows all methods and type schemas for the service in a dict.
        """
        ret: dict = {}
        ret['schema'] = self.schema
        ret['development_mode'] = self.development
        ret['service_info'] = self.info
        return ret
