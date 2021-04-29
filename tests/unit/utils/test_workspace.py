import pytest
import responses
import json

from src.utils.config import config
from src.utils.workspace import ws_auth, get_workspace_info
from src.exceptions import ResponseError

# TODO: All tests should be rewritten to use an explicit service call matcher
# where applicable. This ensures that the precisely correct call has been made.


def service_call_matcher(method, params):
    def match(request_body):
        try:
            if isinstance(request_body, bytes):
                request_body = request_body.decode("utf-8")

            if request_body is None:
                return False

            rpc = json.loads(request_body)

            if rpc['method'] != method:
                return False

            if rpc['params'] != [params]:
                return False

            return True
        except json.JSONDecodeError:
            return False

    return match


mock_ws_ids_with_auth = {
    "version": "1.1",
    "result": [
        {
            "workspaces": [1, 2, 3],
            "pub": [10, 11]
        }
    ]
}

mock_ws_ids_with_auth_only_public = {
    "version": "1.1",
    "result": [
        {
            "workspaces": [],
            "pub": [10, 11]
        }
    ]
}


mock_ws_ids_with_auth_only_private = {
    "version": "1.1",
    "result": [
        {
            "workspaces": [1, 2, 3],
            "pub": []
        }
    ]
}

mock_ws_ids_without_auth = {
    "version": "1.1",
    "result": [
        {
            "workspaces": [],
            "pub": [10, 11]
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

mock_obj_info = {
    "version": "1.1",
    "result": [
        {
            "infos": [
                [
                    87524,
                    "GCF_000314385.1",
                    "KBaseGenomes.Genome-17.0",
                    "2020-07-02T21:06:36+0000",
                    5,
                    "username",
                    15792,
                    "ReferenceDataManager",
                    "3c62af7370ef698c34ce6397dfb5ca81",
                    6193087,
                    None
                ],
                [
                    87515,
                    "GCF_000314305.1",
                    "KBaseGenomes.Genome-17.0",
                    "2020-07-02T21:05:07+0000",
                    5,
                    "username",
                    15792,
                    "ReferenceDataManager",
                    "11360251e96d69ca4b8f857372ce9a02",
                    5858028,
                    None
                ]
            ],
            "paths": [
                [
                    "15792/87524/5"
                ],
                [
                    "15792/87515/5"
                ]
            ]
        }
    ]
}


@responses.activate
def test_ws_auth_valid():
    # Mock the workspace call
    responses.add(responses.POST,
                  config['workspace_url'],
                  headers={'Authorization': 'valid_token'},
                  match=[
                      service_call_matcher(
                          'Workspace.list_workspace_ids',
                          {
                              'perm': 'r',
                              'onlyGlobal': 0,
                              'excludeGlobal': 0
                          }
                      )
                  ],
                  json=mock_ws_ids_with_auth,
                  status=200)
    result = ws_auth('valid_token')
    assert result == [1, 2, 3, 10, 11]


@responses.activate
def test_ws_auth_valid_public():
    responses.add(responses.POST,
                  config['workspace_url'],
                  headers={'Authorization': 'valid_token'},
                  match=[
                      service_call_matcher(
                          'Workspace.list_workspace_ids',
                          {
                              'perm': 'r',
                              'onlyGlobal': 1,
                              'excludeGlobal': 0
                          }
                      )
                  ],
                  json=mock_ws_ids_with_auth_only_public,
                  status=200)
    result = ws_auth('valid_token', only_public=True)
    assert result == [10, 11]


@responses.activate
def test_ws_auth_valid_private():
    # Mock the workspace call
    responses.add(responses.POST,
                  config['workspace_url'],
                  headers={'Authorization': 'valid_token'},
                  match=[
                      service_call_matcher(
                          'Workspace.list_workspace_ids',
                          {
                              'perm': 'r',
                              'onlyGlobal': 0,
                              'excludeGlobal': 1
                          }
                      )
                  ],
                  json=mock_ws_ids_with_auth_only_private,
                  status=200)
    result = ws_auth('valid_token', only_private=True)
    assert result == [1, 2, 3]


def test_ws_auth_error_private_and_public():
    # Mock the workspace call
    with pytest.raises(Exception) as ex:
        ws_auth('valid_token', only_private=True, only_public=True)
    assert 'Only one of "only_public" or "only_private" may be set' in str(ex)


@responses.activate
def test_ws_auth_blank():
    # Mock the workspace call
    responses.add(responses.POST,
                  config['workspace_url'],
                  json=mock_ws_ids_without_auth,
                  status=200)
    result = ws_auth(None)
    assert result == [10, 11]


@responses.activate
def test_ws_auth_invalid():
    # Mock the workspace daily
    responses.add(responses.POST,
                  config['workspace_url'],
                  headers={'Authorization': 'invalid_token'},
                  status=401)
    with pytest.raises(ResponseError) as ctx:
        ws_auth('invalid_token')
    err = ctx.value
    assert err.jsonrpc_code == -32001


@responses.activate
def test_get_workspace_info_valid():
    responses.add(responses.POST,
                  config['workspace_url'],
                  json=mock_ws_info,
                  status=200)
    result = get_workspace_info(1, 'token')
    assert result == mock_ws_info['result'][0]


@responses.activate
def test_get_workspace_info_public():
    responses.add(responses.POST,
                  config['workspace_url'],
                  json=mock_ws_info,
                  status=200)
    result = get_workspace_info(1, None)
    assert result == mock_ws_info['result'][0]


@responses.activate
def test_get_workspace_info_invalid():
    responses.add(responses.POST,
                  config['workspace_url'],
                  status=500)
    with pytest.raises(ResponseError) as ctx:
        get_workspace_info(1, 'token')
    err = ctx.value
    assert err.jsonrpc_code == -32001


@responses.activate
def test_get_workspace_info_invalid2():
    resp = {
        "version": "1.1",
        "result": []
    }
    responses.add(responses.POST,
                  config['workspace_url'],
                  json=resp,
                  status=200)
    with pytest.raises(ResponseError) as ctx:
        get_workspace_info(1, 'token')
    err = ctx.value
    assert err.jsonrpc_code == -32001
    assert len(err.message) > 0
