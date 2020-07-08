"""
Workspace user authentication: find workspaces the user can search
"""
import json
import requests

from src.utils.config import config
from src.exceptions import UnauthorizedAccess


def ws_auth(auth_token):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    if not auth_token:
        return []  # anonymous users
    ws_url = config['workspace_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspace IDs
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
        # TODO raise server error on non-auth error
        raise UnauthorizedAccess(ws_url, resp.text)
    return resp.json()['result'][0]['workspaces']


def get_workspace_info(workspace_id, auth_token):
    """
    Given a list of workspace ids, return the associated workspace info for each one
    """
    if not auth_token:
        # TODO are we sure we want this? Doesn't make a lot of sense
        return []  # anonymous users
    ws_url = config['workspace_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspace IDs
    payload = {
        'method': 'Workspace.get_workspace_info',
        'version': '1.1',
        'params': [{'id': workspace_id}]
    }
    headers = {'Authorization': auth_token}
    resp = requests.post(
        url=ws_url,
        data=json.dumps(payload),
        headers=headers,
    )
    if not resp.ok:
        # TODO better error class
        raise RuntimeError(ws_url, resp.text)
    result = resp.json()['result']
    if not len(result) > 0:
        # TODO better error class
        raise RuntimeError(ws_url, resp.text)
    return result[0]
