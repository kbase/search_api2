"""
Workspace user authentication: find workspaces the user can search
"""
import json
import requests

# from src.utils.config import init_config
# _CONFIG = init_config()

_CONFIG = {
    'elasticsearch': {
        'url': 'http://elasticsearch:9200'
    }
}


class SearchAPILegacy:
    def __init__(self, token, url):
        self.auth_token = token
        self.url = url + '/legacy'

    def call_func(self, method_name, params=None):
        payload = {
            'method': f'KBaseSearchEngine.{method_name}',
            'jsonrpc': '2.0',
            'id': '1234'
        }

        if (params is not None):
            payload['params'] = params

        headers = {'Authorization': self.auth_token}

        response = requests.post(
            url=self.url,
            data=json.dumps(payload),
            headers=headers,
            verify=False,
        )
        if not response.ok:
            raise RuntimeError(self.url, response.text)
        result = response.json()

        if 'error' in result:
            raise RuntimeError(self.url, result['error']['message'])
        return result['result']

    def search_objects(self, params):
        return self.call_func('search_objects', params)

    def search_objects2(self, params):
        return self.call_func('search_objects2', params)

    def search_types(self, params):
        return self.call_func('search_types', params)

    def search_types2(self, params):
        return self.call_func('search_types2', params)

    def list_types(self):
        return self.call_func('list_types')

    def status(self):
        return self.call_func('status')
