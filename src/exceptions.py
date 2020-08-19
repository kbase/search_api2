

class ResponseError(Exception):

    def __init__(self, code=-32000, message='Server error', status=400):
        self.message = message
        self.code = code
        self.status = status


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
        msg = "User profile service error:\nResponse: {resp_text}\nURL: {url}"
        super().__init__(code=-32004, message=msg)
