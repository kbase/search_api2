

class Search2Error(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class UnknownIndex(Search2Error):
    pass


class UnauthorizedAccess(Search2Error):
    "Authentication failed for an authorization header."""

    def __init__(self, auth_url, response):
        self.auth_url = auth_url
        self.response = response
        self.msg = f"Unauthorized for {auth_url}\n{response}"
