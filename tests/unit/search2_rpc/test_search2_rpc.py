"""
Test the RPC service for search2
The RPC module does very little except wrap other methods in a JSONRPCService
object. We test here that things are correctly wrapped, but we don't need to
test search logic here.
"""
import json
import subprocess

from src.search2_rpc import service
from src.utils.wait_for_service import wait_for_service
from tests.helpers import init_elasticsearch

ES_URL = 'http://localhost:9200'
subprocess.run("docker-compose up -d", shell=True)
wait_for_service(ES_URL, 'Elasticsearch')
init_elasticsearch()


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
