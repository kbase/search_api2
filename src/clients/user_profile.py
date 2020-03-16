"""
Workspace user authentication: find workspaces the user can search
"""
import json
import requests

from src.utils.config import init_config

_CONFIG = init_config()


def get_user_profile(usernames, auth_token):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    if not auth_token:
        return []  # anonymous users
    url = _CONFIG['user_profile_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspace IDs
    payload = {
        'method': 'UserProfile.get_user_profile',
        'version': '1.1',
        'params': [usernames]
    }
    headers = {'Authorization': auth_token}
    resp = requests.post(
        url=url,
        data=json.dumps(payload),
        headers=headers,
    )
    if not resp.ok:
        raise RuntimeError(url, resp.text)
    return resp.json()['result'][0]
