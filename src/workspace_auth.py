"""
Workspace user authentication: find workspaces the user can search
"""
import json
import requests

from src.utils.config import init_config

_CONFIG = init_config()


def ws_auth(auth_token):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    if not auth_token:
        return []  # anonymous users
    ws_url = _CONFIG['workspace_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspce IDs
    payload = {
        'method': 'Workspace.list_workspace_ids',
        'version': '1.1',
        'params': [{'perm': 'r'}]
    }
    headers = {'Authorization': auth_token}
    resp = requests.post(
        url=ws_url,
        data=json.dumps(payload),
        headers=headers,
    )
    if not resp.ok:
        raise RuntimeError(ws_url, resp.text)
    return resp.json()['result'][0]['workspaces']
