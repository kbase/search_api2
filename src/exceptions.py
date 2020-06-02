

class UnauthorizedAccess(Exception):
    "Authentication failed for an authorization header."""

    def __init__(self, auth_url, response):
        self.auth_url = auth_url
        self.response = response
