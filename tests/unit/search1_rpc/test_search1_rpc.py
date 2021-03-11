"""
Test the RPC service for search1
The RPC module does very little except wrap other methods in a JSONRPCService
object. We test here that things are correctly wrapped, but we don't need to
test search logic here.
"""
import json
import responses
from src.utils.config import config
from src.search1_rpc import service as rpc
# For mocking workspace calls
from unittest.mock import patch


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
            ],
            "paths": []
        }
    ]
}


@responses.activate
def test_get_objects_valid(services):
    # Mock the obj info request
    responses.add(responses.POST, config['workspace_url'],
                  json=mock_obj_info, status=200)
    # Allow elasticsearch calls
    responses.add_passthru("http://localhost:9200/")
    params = {
        "method": "KBaseSearchEngine.get_objects",
        "version": "1.1",
        "id": 0,
        "params": [
            {
                'guids': ['public-doc1'],
                'post_processing': {'ids_only': 1},
            }
        ],
    }
    result = rpc.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert res['version'] == '1.1'
    assert res['id'] == 0
    assert 'result' in res
    assert len(res['result']) == 1


def ws_call(request):
    header = {
        'Content-Type': 'application/json'
    }
    auth = request.headers.get('Authorization')
    if auth is not None and auth == 'bad_token':
        return (500, header, json.dumps({
            'version': '1.1',
            'id': 'foo',
            'error': {
                'name': 'JSONRPCError',
                'code': -32001,
                'message': 'INVALID TOKEN'
            }
        }))
    else:
        return 200, header, json.dumps(mock_obj_info)


@responses.activate
def test_get_objects_bad_auth(services):
    # Mock the obj info request
    responses.add_callback(responses.POST,
                           config['workspace_url'],
                           callback=ws_call)
    # Allow elasticsearch calls
    responses.add_passthru("http://localhost:9200/")
    params = {
        "method": "KBaseSearchEngine.get_objects",
        "version": "1.1",
        "params": [
            {
                'guids': ['public-doc1'],
                'post_processing': {'ids_only': 1},
            }
        ],
    }
    result = rpc.call(json.dumps(params), {'auth': 'bad_token'})
    res = json.loads(result)
    assert res['version'] == '1.1'
    assert 'error' in res
    error = res['error']
    assert error['code'] == -32001
    assert error['message'] == 'Auth error'
    assert error['name'] == 'JSONRPCError'


def test_search_objects_valid(services):
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [0, 1]  # Public workspaces
        params = {
            "method": "KBaseSearchEngine.search_objects",
            "version": "1.1",
            "id": 0,
            "params": [{
                'match_filter': {},
                'pagination': {'count': 0, 'start': 0},
            }]
        }
        result = rpc.call(json.dumps(params), {'auth': None})
        res = json.loads(result)
        assert 'result' in res
        assert len(res['result']) == 1


def test_search_types_valid(services):
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [0, 1]  # Public workspaces
        params = {
            "method": "KBaseSearchEngine.search_types",
            "version": "1.1",
            "id": "0",
            "params": [{'object_types': ['x'], 'match_filter': {}}]
        }
        result = rpc.call(json.dumps(params), {'auth': None})
        res = json.loads(result)
        assert 'result' in res
        assert len(res['result']) == 1
