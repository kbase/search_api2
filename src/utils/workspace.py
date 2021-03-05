"""
Workspace user authentication: find workspaces the user can search
"""
import json
import requests
from typing import Optional

from src.utils.config import config
from src.exceptions import AuthError


def ws_auth(auth_token, only_public=False, only_private=False):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their
    # readable workspace IDs
    params = {
        'perm': 'r'
    }

    if only_public:
        if only_private:
            raise Exception('Only one of "only_public" or "only_private" may be set')
        params['onlyGlobal'] = 1
        params['excludeGlobal'] = 0
    elif only_private:
        params['onlyGlobal'] = 0
        params['excludeGlobal'] = 1
    else:
        params['onlyGlobal'] = 0
        params['excludeGlobal'] = 0

    result = _req('list_workspace_ids', params, auth_token)
    return result.get('workspaces', []) + result.get('pub', [])


def get_workspace_info(workspace_id, auth_token=None):
    """
    Given a workspace id, return the associated workspace info
    """
    # TODO session cache this
    params = {'id': workspace_id}
    return _req('get_workspace_info', params, auth_token)


def _req(method: str, params: dict, token: Optional[str]):
    """Make a generic workspace http/rpc request"""
    payload = {
        'method': 'Workspace.' + method,
        'version': '1.1',
        'id': 0,
        'params': [params],
    }

    headers = {}
    if token is not None:
        headers['Authorization'] = token

    resp = requests.post(
        url=config['workspace_url'],
        headers=headers,
        data=json.dumps(payload),
    )
    resp_json = None
    result = None
    try:
        result = resp.json().get('result')
        resp_json = resp.json()
    except json.decoder.JSONDecodeError:
        pass
    if not resp.ok or not result or len(result) == 0:
        raise AuthError(resp_json, resp.text)
    return result[0]
