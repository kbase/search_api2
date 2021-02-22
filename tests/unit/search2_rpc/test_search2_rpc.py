"""
Test the RPC service for search2
The RPC module does very little except wrap other methods in a JSONRPCService
object. We test here that things are correctly wrapped, but we don't need to
test search logic here.
"""
import json

from src.search2_rpc import service
from tests.helpers import init_elasticsearch

from tests.helpers.unit_setup import (
    start_service,
    stop_service
)

ES_URL = 'http://localhost:9200'
APP_URL = 'http://localhost:5000'


def setup_module(module):
    start_service(APP_URL, 'searchapi2')
    init_elasticsearch()


def teardown_module(module):
    stop_service()


def test_show_indexes():
    params = {
        "method": "show_indexes",
        "jsonrpc": "2.0",
        "id": 0,
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert res['result']


def test_show_config():
    params = {
        "method": "show_config",
        "jsonrpc": "2.0",
        "id": 0,
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert res['result']


def test_search_objects():
    params = {
        "method": "search_objects",
        "jsonrpc": "2.0",
        "id": 0,
        "params": {}
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert res['result']['count'] > 0


def test_search_workspace():
    params = {
        "method": "search_workspace",
        "jsonrpc": "2.0",
        "id": 0,
        "params": {
            "types": ["KBaseNarrative.Narrative"]
        }
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert 'error' not in res
    assert res['result']['count'] > 0
