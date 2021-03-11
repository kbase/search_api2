from jsonrpc11base.errors import APIError
from src import exceptions


class UnknownTypeError(APIError):
    code = 1000
    message = 'Unknown type'

    def __init__(self, message):
        self.error = {
            'message': message
        }


class AuthorizationError(APIError):
    code = 2000
    message = 'Auth error'

    def __init__(self, message):
        self.error = {
            'message': message
        }


class UnknownIndexError(APIError):
    code = 3000
    message = 'Unknown index'

    def __init__(self, message):
        self.error = {
            'message': message
        }


class ElasticsearchServerError(APIError):
    code = 4000
    message = 'Elasticsearch server error'

    def __init__(self, message):
        self.error = {
            'message': message
        }

# def __init__(self, url, resp_text):
#     msg = f"User profile service error:\nResponse: {resp_text}\nURL: {url}"
#     super().__init__(code=-32004, message=msg)


class UserProfileServiceError(APIError):
    code = 50000
    message = 'User profile service error'

    def __init__(self, url, resp_text):
        self.error = {
            'url': url,
            'resp_text': resp_text
        }

    def __str__(self):
        return f"{self.message}\nResponse: {self.error['resp_text']}\nURL: {self.error['url']}"


def trap_error(fun):
    try:
        return fun()
    except exceptions.UnknownType as ut:
        raise UnknownTypeError(ut.message)
    except exceptions.AuthError as ae:
        raise AuthorizationError(ae.message)
    except exceptions.ElasticsearchError as ee:
        raise ElasticsearchServerError(ee.message)
    except exceptions.UnknownIndex as ue:
        raise UnknownIndexError(ue.message)
    except exceptions.UserProfileError as upe:
        raise UserProfileServiceError(upe.url, upe.resp_text)
