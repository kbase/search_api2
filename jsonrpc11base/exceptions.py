"""
Exception classes
"""


class JSONRPCBaseError(RuntimeError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InvalidSchemaError(JSONRPCBaseError):
    """Invalid JSON-Schema data."""
    pass


class InvalidServerErrorCode(JSONRPCBaseError):
    """Invalid custom server error code (must be -32000 - -32099)."""
    pass


class DuplicateMethodName(JSONRPCBaseError):
    """User tried to register two methods of the same name to the same service."""
    pass


class InvalidFileType(JSONRPCBaseError):
    """Invalid file extension"""
    pass
