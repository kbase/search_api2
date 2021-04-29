"""
Test the RPC service for search2
The RPC module does very little except wrap other methods in a JSONRPCService
object. We test here that things are correctly wrapped, but we don't need to
test search logic here.
"""
import json
# For mocking workspace calls
from unittest.mock import patch
from src.search2_rpc import service as rpc


def test_show_indexes(services):
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [0, 1]  # Public workspaces
        params = {
            "method": "show_indexes",
            "jsonrpc": "2.0",
            "id": 0,
        }
        result = rpc.call(json.dumps(params), {'auth': None})
        res = json.loads(result)
        assert res['result']


def test_show_indexes_not_found(services):
    with patch.dict('src.utils.config.config', {'index_prefix': 'foo'}):
        with patch('src.es_client.query.ws_auth') as mocked:
            mocked.return_value = [0, 1]  # Public workspaces
            params = {
                "method": "show_indexes",
                "jsonrpc": "2.0",
                "id": 0,
            }
            result = rpc.call(json.dumps(params), {'auth': None})
            res = json.loads(result)
            assert len(res['result']) == 0


def test_show_indexes_error(services):
    with patch.dict('src.utils.config.config', {'index_prefix': '/'}):
        with patch('src.es_client.query.ws_auth') as mocked:
            mocked.return_value = [0, 1]  # Public workspaces
            params = {
                "method": "show_indexes",
                "jsonrpc": "2.0",
                "id": 0,
            }
            result = rpc.call(json.dumps(params), {'auth': None})
            res = json.loads(result)
            assert res['error']
            assert res['error']['code'] == -32003
            assert res['error']['message'] == 'Server error'
            assert res['error']['data']['method'] == 'show_indexes'


def test_show_config(services):
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [0, 1]  # Public workspaces
        params = {
            "method": "show_config",
            "jsonrpc": "2.0",
            "id": 0,
        }
        result = rpc.call(json.dumps(params), {'auth': None})
        res = json.loads(result)
        assert res['result']


def test_search_objects(services):
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [0, 1]  # Public workspaces
        params = {
            "method": "search_objects",
            "jsonrpc": "2.0",
            "id": 0,
            "params": {}
        }
        result = rpc.call(json.dumps(params), {'auth': None})
        res = json.loads(result)
        assert res['result']['count'] > 0


def test_search_workspace(services):
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [0, 1]  # Public workspaces
        params = {
            "method": "search_workspace",
            "jsonrpc": "2.0",
            "id": 0,
            "params": {
                "types": ["KBaseNarrative.Narrative"]
            }
        }
        result = rpc.call(json.dumps(params), {'auth': None})
        res = json.loads(result)
        assert 'error' not in res
        assert res['result']['count'] > 0
