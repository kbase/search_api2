import pytest
import responses

from src.exceptions import UnauthorizedAccess
from src.utils.config import config
from src.utils.workspace import ws_auth, get_workspace_info

mock_ws_ids = {
  "version": "1.1",
  "result": [
    {
      "workspaces": [1, 2, 3],
      "pub": []
    }
  ]
}

mock_ws_info = {
    "version": "1.1",
    "result": [[
        1,
        "test_workspace",
        "username",
        "2020-06-06T03:49:55+0000",
        388422,
        "n",
        "r",
        "unlocked",
        {
            "searchtags": "refdata"
        }
    ]]
}


@responses.activate
def test_ws_auth_valid():
    # Mock the workspace call
    responses.add(responses.POST, config['workspace_url'],
                  json=mock_ws_ids, status=200)
    result = ws_auth('valid_token')
    assert result == [1, 2, 3]


def test_ws_auth_blank():
    result = ws_auth(None)
    assert result == []


@responses.activate
def test_ws_auth_invalid():
    # Mock the workspace call
    responses.add(responses.POST, config['workspace_url'], status=403)
    with pytest.raises(UnauthorizedAccess):
        ws_auth('x')


@responses.activate
def test_get_workspace_info_valid():
    responses.add(responses.POST, config['workspace_url'],
                  json=mock_ws_info, status=200)
    result = get_workspace_info(1, 'token')
    assert result == mock_ws_info['result'][0]


def test_get_workspace_info_blank():
    result = get_workspace_info(1, None)
    assert result == []


@responses.activate
def test_get_workspace_info_invalid():
    responses.add(responses.POST, config['workspace_url'], status=500)
    with pytest.raises(RuntimeError):
        get_workspace_info(1, 'token')


@responses.activate
def test_get_workspace_info_invalid2():
    resp = {
        "version": "1.1", "result": []
    }
    responses.add(responses.POST, config['workspace_url'],
                  json=resp, status=200)
    with pytest.raises(RuntimeError):
        get_workspace_info(1, 'token')
