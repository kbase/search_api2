import pytest
import responses

from src.utils.config import config
from src.utils.user_profiles import get_user_profiles
from src.exceptions import UserProfileError


mock_resp = {
    "version": "1.1",
    "result": [[{
        "user": {
            "username": "username",
            "realname": "User Example"
        },
        "profile": {}
    }]]
}


@responses.activate
def test_get_user_profiles_valid():
    responses.add(responses.POST, config['user_profile_url'],
                  headers={'Authorization': 'x'},
                  json=mock_resp, status=200)
    res = get_user_profiles(['username'], 'x')
    assert res == mock_resp['result'][0]


@responses.activate
def test_get_user_profiles_noauth():
    responses.add(responses.POST, config['user_profile_url'],
                  json=mock_resp, status=200)
    res = get_user_profiles(['username'], None)
    assert res == mock_resp['result'][0]


@responses.activate
def test_get_user_profiles_invalid():
    responses.add(responses.POST, config['user_profile_url'], status=400)
    with pytest.raises(UserProfileError):
        get_user_profiles(['username'], 'x')
