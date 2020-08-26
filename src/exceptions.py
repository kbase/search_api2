from src.utils.obj_utils import get_path


class ResponseError(Exception):

    def __init__(self, code=-32000, message='Server error'):
        self.message = message
        self.jsonrpc_code = code


class UnknownType(ResponseError):

    def __init__(self, message):
        super().__init__(code=-32005, message=message)


class ElasticsearchError(ResponseError):

    def __init__(self, message):
        msg = f"Elasticsearch request error:\n{message}"
        super().__init__(code=-32003, message=msg)


class UnknownIndex(ResponseError):

    def __init__(self, message):
        super().__init__(code=-32002, message=message)


class UserProfileError(ResponseError):

    def __init__(self, url, resp_text):
        msg = f"User profile service error:\nResponse: {resp_text}\nURL: {url}"
        super().__init__(code=-32004, message=msg)


class AuthError(ResponseError):

    def __init__(self, resp_json, resp_text):
        # Extract the error message from the RPC response
        msg = get_path(resp_json, ['error', 'message'])
        if msg is None:
            # Fall back to the full response body
            msg = resp_text
        super().__init__(code=-32001, message=msg)
