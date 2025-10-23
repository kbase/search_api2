"""
Simple JSON-RPC service without transport layer

See README.md for details

Uses Google Style Python docstrings:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
"""
from jsonrpc11base.service_description import ServiceDescription
import jsonrpc11base.validation.validation as validation
import json
import os
import logging

from typing import Callable, Optional, Union, Dict

import jsonrpc11base.exceptions as exceptions
import traceback
from jsonrpc11base.validation.schema import Schema, SchemaError
from jsonrpc11base.errors import (make_standard_jsonrpc_error, make_custom_jsonrpc_error,
                                  make_jsonrpc_error_response,
                                  InvalidParamsError, JSONRPCError, APIError,
                                  MethodNotFoundError,
                                  ReservedErrorCodeServerError, InvalidResultServerError)
from jsonrpc11base.types import (MethodRequest, MethodResult)
from jsonrpc11base.method import Method

log = logging.getLogger(__name__)


class JSONRPCService(object):
    """
    The JSONRPCService class is a JSON-RPC 1.1 implementation
    """
    def __init__(self,
                 description: ServiceDescription,
                 schema_dir: Optional[Union[str, None]] = None,
                 validate_params: bool = False,
                 validate_result: bool = False):
        """
        Initialize a new JSONRPCService object.

        Args:
            description: A ServiceDescription instance
            schema_dir: A directory path in which service schemas
                        may be found
            validate_params: A boolean flag controlling whether parameters are
                        validated or not; defaults to False
            validate_result: A boolean flag controlling whether the result is
                        validated or not; defaults  to False
        """
        # Initialize global jsonrpc schemas, which validate the overall
        # JSON-RPC 1.1 structures. These schemas are built-in.
        self.jsonrpc_schemas = Schema(os.path.abspath(
            os.path.dirname(__file__) + '/jsonrpc_schema'))

        # Load the optional service validation jsonschemas. If no schemas
        # are provided in the schema directory, service params and results
        # are not validated.
        if schema_dir is not None:
            self.service_validation = validation.Validation(schema_dir=schema_dir)
        else:
            self.service_validation = None

        system_schema_dir = os.path.abspath(
            os.path.dirname(__file__) + '/system_schema')
        self.system_validation = validation.Validation(schema_dir=system_schema_dir)

        self.method_registry: Dict[str, Method] = {}
        self.system_method_registry: Dict[str, Method] = {}

        # Add the built-in "system.describe" method
        self.add(self.handle_system_describe, 'system.describe', system=True)

        if self.service_validation is None:
            if validate_params:
                raise TypeError('May not validate params with no schema_dir provided')
            if validate_result:
                raise TypeError('May not validate result with no schema_dir provided')

        self.validate_params = validate_params
        self.validate_result = validate_result

        self.description = description

    def add(self, func: Callable, name: Optional[str] = None, system: bool = False):
        """
        Adds a new method to the jsonrpc service. If name argument is not
        given, function's own name will be used.

        Example:
            service.add(myfunc, name='my_function')

        Args:
            func: required python function handler to call for this method
            name: name of the method (optional, defaults to the function's name)
        """
        function_name = name if name else func.__name__
        registry = self.method_registry if not system else self.system_method_registry
        if function_name in registry:
            msg = f'Method "{function_name}" already registered'
            raise exceptions.DuplicateMethodName(msg)
        registry[function_name] = Method(func)

    def call(self, jsondata: str, options=None) -> str:
        """
        Calls jsonrpc service's method and returns its return value in a JSON
        string or None if there is none.

        Args:
           jsondata: JSON-RPC 1.1 request body (raw string)
           options: any additional object to pass along to the handler function as the second arg

        Returns:
            The JSON-RPC 1.1 response as a raw JSON string.
            Will not throw an exception.
        """
        try:
            request_data = json.loads(jsondata)
        except ValueError as err:
            resp = make_jsonrpc_error_response(
                make_standard_jsonrpc_error(-32700, error={'message': str(err)}))
            return json.dumps(resp)

        result = self.call_py(request_data, options)
        if result is not None:
            return json.dumps(result)

    def find_method(self, method_name):
        method_parts = method_name.split('.')

        is_system_method = False
        if len(method_parts) == 2:
            if method_parts[0] == 'system':
                is_system_method = True

        registry = self.method_registry if not is_system_method else self.system_method_registry

        if method_name not in registry:
            methods = list(registry.keys())
            raise MethodNotFoundError(method=method_name, available_methods=methods)

        return [registry[method_name], is_system_method]

    # Wraps the process of method invocation and validation
    def do_method(self, method_name, params, options):
        method, is_system_method = self.find_method(method_name)

        if is_system_method:
            validator = self.system_validation
        else:
            validator = self.service_validation

        if validator is not None:
            if validator.has_params_validation(method_name):
                if params is None:
                    raise InvalidParamsError(
                        message='Method has parameters specified, but none were provided'
                    )
                else:
                    validator.validate_params(method_name, params)
                    return [method.call(params, options), is_system_method]
            elif validator.has_absent_params_validation(method_name):
                if params is None:
                    validator.validate_absent_params(method_name)
                    return [method.call(None, options), is_system_method]
                else:
                    raise InvalidParamsError(
                        message=('Method has no parameters specified, '
                                 'but arguments were provided')
                    )
            else:
                # If validation is provided, all methods must have validation.
                raise InvalidParamsError(
                    message='Validation is enabled, but no parameter validator was provided'
                )
        else:
            return [method.call(params, options), is_system_method]

    def call_py(self, req_data: MethodRequest, options=None) -> MethodResult:
        """
        Call a method in the service and return the RPC response. The _py suffix indicates
        that input and output are Python objects, not strings. In other words, the "call"
        method wraps "call_py" by dealing with strings, allowing "call_py" to ignore JSON
        conversion.

        Args:
            req_data: JSON-RPC 1.1 request data as a python object
            options: Any optional additional, application-specific data, which will be
            passed straight through to the rpc method.

        Returns:
            The JSON-RPC 1.1 response as a python object.
            Will not throw an exception.
        """
        # Validate the request data using a json-schema
        try:
            if self.validate_params:
                self.jsonrpc_schemas.validate('request', req_data)
        except SchemaError as ex:
            error = make_standard_jsonrpc_error(-32600, error={
                'message': ex.message,
                'path': ex.path,
                'value': ex.value
            })
            # May seem pointless, but in case the request does not validate, yet it is an
            # object, it might have an id  to use in the response.
            if isinstance(req_data, dict):
                return make_jsonrpc_error_response(error, req_data.get('id'))
            else:
                return make_jsonrpc_error_response(error)

        request_id = req_data.get('id')

        # Note that we can be cavalier, assuming that the 'method'
        # is available in the request, since we've already validated it,
        # and 'method' is required.
        method_name = req_data['method']

        # Note that  params is optional, but must be a JSON
        # array or object (enforced with the jsonschema), so
        # if it is absent, and thus None here, we know it isn't
        # JSON null, and None really means none (and is not the
        # imo misuse of None for JSON null)
        params = req_data.get('params')

        # Wraps the process of results validation
        def do_result(result, system_method):
            if not self.validate_result:
                return result

            if system_method:
                validator = self.system_validation
            else:
                validator = self.service_validation

            if not validator.has_result_validation(method_name):
                # If validation is provided, all methods must have validation.
                raise InvalidParamsError(
                    message='Validation is enabled, but no result validator was provided'
                )

            if validator.has_absent_result_validation(method_name):
                # If the method should have no result, we just set it to null.
                # JSONRPC 1.1 mentions the value 'nil' for methods without a result
                # value, but the result is also required, so we need to populate
                # it with something ... null is a good choice.
                # The caller should ignore the value.
                if result is None:
                    return None
                else:
                    raise InvalidResultServerError(
                        message=('The method is specified to not return a result, '
                                 'yet a value was returned'),
                        value=result
                    )

            validator.validate_result(method_name, result)
            return result

        # Wraps the process of creating a result
        def make_result_response(result):
            response_data = {
                'version': '1.1',
                'result': result
            }
            if request_id is not None:
                response_data['id'] = request_id
            return response_data

        # Wraps error object construction
        def make_error_response(error_data):
            # From closure
            if 'error' not in error_data:
                error_data['error'] = {}
            error_data['error']['method'] = method_name

            return make_jsonrpc_error_response(error_data, request_id)

        try:
            result, system_method = self.do_method(method_name, params, options)
            return make_result_response(do_result(result, system_method))
        # Covers a method throwing any specific jsonrpc predefined
        # exception.
        except JSONRPCError as e:
            return make_error_response(e.to_json())
        # Covers a method throwing a jsonrpc error which is not
        # within the range of predefined jsonrpc errors
        except APIError as e:
            # Which, sigh, itself may be an error if the app used
            # an error code within the reserved range.
            if -32768 <= e.code <= -32000:
                err = ReservedErrorCodeServerError(
                    message=(
                        'An error code  was issued by the api which conflicts with ',
                        'the reserved range between -32768 and -3200'
                    ),
                    bad_code=e.code
                )
                return make_error_response(err.to_json())
            else:
                return make_error_response(e.to_json())
        # Finally, catch any programming errors
        except Exception as ex:
            message = getattr(ex, 'message', str(ex))
            error = {'message': ('An unexpected exception was caught '
                                 'executing the method'),
                     'exception_message': message or 'Unknown exception',
                     'traceback': traceback.format_exc(limit=1000).split('\n')}
            error = make_custom_jsonrpc_error(-32002,
                                              message='Exception calling method',
                                              error=error)
            return make_error_response(error)

    # TODO: break off into a service class

    # TODO: move to a service module

    def handle_system_describe(self, options) -> dict:
        """
        Built-in method handler that shows all methods and type schemas for the service in a dict.
        """
        return self.description.to_json()
