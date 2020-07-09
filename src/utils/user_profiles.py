import json
import requests

from src.utils.config import config


def get_user_profiles(usernames: list, auth_token):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    if not auth_token:
        return []  # anonymous users
    url = config['user_profile_url']
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
        # TODO better error class
        raise RuntimeError(url, resp.text)
    return resp.json()['result'][0]