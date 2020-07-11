"""
Test the RPC service for search1
The RPC module does very little except wrap other methods in a JSONRPCService
object. We test here that things are correctly wrapped, but we don't need to
test search logic here.
"""
import json
import subprocess

from src.search1_rpc import service
from src.utils.wait_for_service import wait_for_service
from tests.helpers import init_elasticsearch

ES_URL = 'http://localhost:9200'
subprocess.run("docker-compose up -d", shell=True)
wait_for_service(ES_URL, 'Elasticsearch')
init_elasticsearch()


def test_get_objects_valid():
    params = {
        "method": "KBaseSearchEngine.get_objects",
        "jsonrpc": "2.0",
        "id": 0,
        "params": [{'guids': ['public-doc1']}],
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert len(res['result']) == 1


def test_search_objects_valid():
    params = {
        "method": "KBaseSearchEngine.search_objects",
        "jsonrpc": "2.0",
        "id": 0,
        "params": [{'match_filter': {}}]
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert len(res['result']) == 1


def test_search_types_valid():
    params = {
        "method": "KBaseSearchEngine.search_types",
        "jsonrpc": "2.0",
        "id": "0",
        "params": [{'object_types': ['x'], 'match_filter': {}}]
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert len(res['result']) == 1
