from src.utils.obj_utils import get_path


# TODO: we should use the jsonrpc11base libraries base exception for
# server errors
class ResponseError(Exception):

    def __init__(self, code=-32000, message='Server error'):
        self.message = message
        self.jsonrpc_code = code


class AuthError(ResponseError):

    def __init__(self, auth_resp_json, resp_text):
        # Extract the error message from the auth service's RPC response
        msg = get_path(auth_resp_json, ['error', 'message'])
        if msg is None:
            # Fall back to the full response body
            msg = resp_text
        super().__init__(code=-32001, message=msg)


class UnknownIndex(ResponseError):

    def __init__(self, message):
        super().__init__(code=-32002, message=message)


class ElasticsearchError(ResponseError):

    def __init__(self, message):
        msg = f"Elasticsearch request error:\n{message}"
        super().__init__(code=-32003, message=msg)


class UserProfileError(ResponseError):

    def __init__(self, url, resp_text):
        self.url = url
        self.resp_text = resp_text
        msg = f"User profile service error:\nResponse: {resp_text}\nURL: {url}"
        super().__init__(code=-32004, message=msg)


class UnknownType(ResponseError):

    def __init__(self, message) -> object:
        super().__init__(code=-32005, message=message)


class NoAccessGroupError(ResponseError):
    """
    Raised when a search result does not contain an "access_group"
    key, which should be impossible.
    """

    def __init__(self):
        message = 'A search document does not contain an access group'
        super().__init__(code=-32006, message=message)


class NoUserProfileError(ResponseError):
    """
    Raised when a username does not have an associated user profile.
    """

    def __init__(self, username):
        message = f'A user profile could not be found for "{username}"'
        super().__init__(code=-32007, message=message)
