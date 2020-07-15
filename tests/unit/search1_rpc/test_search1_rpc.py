"""
Test the RPC service for search1
The RPC module does very little except wrap other methods in a JSONRPCService
object. We test here that things are correctly wrapped, but we don't need to
test search logic here.
"""
import json
import responses
import subprocess

from src.search1_rpc import service
from src.utils.config import config
from src.utils.wait_for_service import wait_for_service
from tests.helpers import init_elasticsearch

ES_URL = 'http://localhost:9200'
subprocess.run("docker-compose up -d", shell=True)
wait_for_service(ES_URL, 'Elasticsearch')
init_elasticsearch()
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
def test_get_objects_valid():
    # Mock the obj info request
    responses.add(responses.POST, config['workspace_url'],
                  json=mock_obj_info, status=200)
    # Allow elasticsearch calls
    responses.add_passthru("http://localhost:9200/")
    params = {
        "method": "KBaseSearchEngine.get_objects",
        "jsonrpc": "2.0",
        "id": 0,
        "params": [
            {
                'guids': ['public-doc1'],
                'post_processing': {'ids_only': 1},
            }
        ],
    }
    result = service.call(json.dumps(params), {'auth': None})
    res = json.loads(result)
    assert res['jsonrpc'] == '2.0'
    assert res['id'] == 0
    assert len(res['result']) == 1


def test_search_objects_valid():
    params = {
        "method": "KBaseSearchEngine.search_objects",
        "jsonrpc": "2.0",
        "id": 0,
        "params": [{
            'match_filter': {},
            'pagination': {'count': 0, 'start': 0},
        }]
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
