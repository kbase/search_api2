import json
import requests

from src.utils.config import config
from src.exceptions import UserProfileError


def get_user_profiles(usernames: list, auth_token=None):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    url = config['user_profile_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspace IDs
    payload = {
        'method': 'UserProfile.get_user_profile',
        'version': '1.1',
        'params': [usernames]
    }
    headers = {}
    if auth_token is not None:
        headers['Authorization'] = auth_token
    resp = requests.post(
        url=url,
        data=json.dumps(payload),
        headers=headers,
    )
    if not resp.ok:
        raise UserProfileError(url, resp.text)
    return resp.json()['result'][0]
