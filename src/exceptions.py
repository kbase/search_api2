

class InvalidJSON(Exception):
    """Invalid JSON syntax."""

    def __init__(self, msg): self.msg = msg

    def __str__(self): return self.msg


class InvalidParameters(Exception):
    """
    Invalid request parameters.
    Saves the JSON RPC request ID and a jsonschema validation error object.
    """

    def __init__(self, jsonschema_err, request_id):
        self.request_id = request_id
        self.jsonschema_err = jsonschema_err

    def __str__(self):
        return self.msg


class UnknownMethod(Exception):
    """Unrecognized RPC method."""

    def __init__(self, method, request_id):
        self.method = method
        self.request_id = request_id


class UnauthorizedAccess(Exception):
    "Authentication failed for an authorization header."""

    def __init__(self, auth_url, response):
        self.auth_url = auth_url
        self.response = response
