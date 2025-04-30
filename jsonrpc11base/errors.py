from typing import Optional
from jsonrpc11base.types import Identifier


# ===============================================================================
# Errors
#
# The error-codes -32768 .. -32000 (inclusive) are reserved for pre-defined
# errors.
#
# Any error-code within this range not defined explicitly below is reserved
# for future use
# ===============================================================================

# Reference: https://www.jsonrpc.org/specification#error_object
RPC_ERRORS = {
    # Invalid JSON was received. An error occurred on the server while parsing the JSON text.
    -32700: 'Parse error',
    # The JSON sent is not a valid Request object.
    # Note that this message uses proper-cased "Request", as per the spec. This is the one
    # exception to sentence-casing for error messages.
    -32600: 'Invalid Request',
    # The method does not exist / is not available.
    -32601: 'Method not found',
    # Invalid method parameter(s).
    -32602: 'Invalid params',
    # Internal JSON-RPC error.
    -32603: 'Internal error',
    # -32000 to -32099 to Reserved for implementation-defined server-errors.
    # Unspecified, but should have it's own error message
    -32000: 'Server error'
}


class JSONRPCError(Exception):
    """
    JSONRPCError class based on the JSON-RPC 2.0 specs.

    code - number
    message - string
    data - object
    """
    code: int = 0
    message: Optional[str] = None
    error: Optional[dict] = None

    def to_json(self):
        """Return the Exception data in a format for JSON-RPC."""

        error = {'name': 'JSONRPCError',
                 'code': self.code,
                 'message': str(self.message)}

        if self.error is not None:
            error['error'] = self.error

        return error

# Standard Errors


class ParseError(JSONRPCError):
    """Invalid JSON. An error occurred on the server while parsing the JSON text."""
    code = -32700
    message = 'Parse error'


class InvalidRequestError(JSONRPCError):
    """The received JSON is not a valid JSON-RPC Request."""
    code = -32600
    message = 'Invalid Request'


class MethodNotFoundError(JSONRPCError):
    """The requested remote-procedure does not exist / is not available."""
    code = -32601
    message = 'Method not found'

    def __init__(self, method, available_methods):
        self.error = {
            'method': method,
            'available_methods': available_methods
        }


class InvalidParamsError(JSONRPCError):
    """Invalid method parameters."""
    code = -32602
    message = 'Invalid params'

    def __init__(self, message=None, path=None, value=None):
        self.error = {}
        if message is not None:
            self.error['message'] = message
        if path is not None:
            self.error['path'] = path
        if value is not None:
            self.error['value'] = value


class InternalError(JSONRPCError):
    """Internal JSON-RPC error."""
    code = -32603
    message = 'Internal error'


# Server Errors
# The server may specify any additional errors from -32000 to -32099.


class ServerError(JSONRPCError):
    """Implementation defined server error -32000 through -32099"""
    code = -32000
    message = 'Server error'

    def __init__(self, message):
        self.error = {
            'message': message
        }


class ReservedErrorCodeServerError(ServerError):
    """Generic server error."""
    code = -32001
    message = 'Reserved error code'

    def __init__(self, message, bad_code=None):
        super().__init__(message)
        if bad_code is not None:
            self.error['bad_code'] = bad_code


class InvalidResultServerError(ServerError):
    """Generic server error."""
    code = -32002
    message = 'Invalid result'

    def __init__(self, message, path=None, value=None):
        super().__init__(message)
        if path is not None:
            self.error['path'] = path
        if value is not None:
            self.error['value'] = value

#
# class ServerError_AuthenticationRequired(CustomServerError):
#     """Generic server error."""
#     code = -32003
#     message = 'Authentication required'


# The api may use any error code outside the reserved range -32000 too -32768.
# The api should subclass the APIError exception for each type of
# error and associate a code with that error.


class APIError(Exception):
    """
    APIError class based on the JSON-RPC 1.1 specs.
    Should not be used directly, but subclassed.

    code - number
    message - string
    error - object
    """
    code: int = 1
    message: str = 'API error'
    error: Optional[dict] = None

    def to_json(self):
        """Return the Exception data in a format for JSON-RPC."""

        error = {'name': 'APIError',
                 'code': self.code,
                 'message': self.message}

        if self.error is not None:
            error['error'] = self.error

        return error


def make_standard_jsonrpc_error(code: int,
                                error: Optional[dict] = None):
    """
    Makes a JRON-RPC 1.1. compliant error
    """
    jsonrpc_error = {
        'name': 'JSONRPCError',
        'code': code,
        'message': RPC_ERRORS[code]
    }

    if error is not None:
        jsonrpc_error['error'] = error

    return jsonrpc_error


def make_custom_jsonrpc_error(code: int,
                              message: Optional[str],
                              error: Optional[dict] = None):
    """
    Makes a JRON-RPC 1.1. compliant error
    """

    jsonrpc_error = {
        'name': 'JSONRPCError',
        'code': code,
        'message': message
    }

    if error is not None:
        jsonrpc_error['error'] = error

    return jsonrpc_error


def make_jsonrpc_error_response(error: Optional[dict],
                                id: Optional[Identifier] = None):
    """
    Makes a JRON-RPC 1.1. compliant error
    """

    response_data = {
        'version': '1.1',
        'error': error
    }

    if id is not None:
        response_data['id'] = id

    return response_data
