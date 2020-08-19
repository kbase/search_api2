import json
import requests
import subprocess

from src.utils.wait_for_service import wait_for_service
import tests.helpers as helpers

BASE_URL = "http://localhost:5000"

# Start the services
# This implicitly tests the "/" path
subprocess.run("docker-compose up -d", shell=True)
wait_for_service(BASE_URL, "search2")
helpers.init_elasticsearch()


def test_rpc_valid():
    """Test a basic valid request to /rpc"""
    resp = requests.post(
        BASE_URL + '/rpc',
        data=json.dumps({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "show_config",
        })
    )
    result = resp.json()
    assert result['id'] == 0
    assert result['jsonrpc'] == '2.0'
    assert result['result']['dev']


def test_auth_fail_resp():
    resp = requests.post(
        BASE_URL + "/legacy",
        headers={"Authorization": "xyz"},
        data=json.dumps({
            "jsonrpc": "2.0",
            "id": "0",
            "method": "KBaseSearchEngine.get_objects",
            "params": [{"guids": ["xyz"]}],
        })
    )
    result = resp.json()
    assert result['error']['code'] == -32001
    assert resp.status_code == 400
    print(resp.text)


def test_legacy_valid():
    """Test a basic valid request to /legacy"""
    resp = requests.post(
        BASE_URL + '/legacy',
        data=json.dumps({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    print(json.dumps(resp.json(), indent=4))
    assert resp.status_code == 200
    result = resp.json()
    assert result['id'] == 0
    assert result['jsonrpc'] == '2.0'
    assert len(result['result']) == 1


def test_rpc_invalid():
    """Test a basic empty request to /rpc"""
    resp = requests.get(BASE_URL + '/rpc')
    assert resp.json()['error']['code'] == -32600  # Invalid params


def test_legacy_invalid():
    """Test a basic empty request to /legacy"""
    resp = requests.get(BASE_URL + '/legacy')
    assert resp.json()['error']['code'] == -32600  # Invalid params


def test_handle_options():
    """Handle a cors-style options requests on all paths"""
    paths = ['/', '/rpc', '/status', '/legacy']
    for path in paths:
        resp = requests.options(BASE_URL + path)
        assert resp.status_code == 204
        assert resp.text == ''
        assert resp.headers['Access-Control-Allow-Origin'] == '*'
        assert resp.headers['Access-Control-Allow-Methods'] == 'POST, GET, OPTIONS'
        assert resp.headers['Access-Control-Allow-Headers'] == '*'


def test_404():
    resp = requests.get(BASE_URL + '/xyz')
    assert resp.status_code == 404
    assert resp.text == ''


def test_legacy_rpc_conversion():
    """
    Test that a JSON-RPC 1.1 request is still handled ok
    """
    resp = requests.post(
        BASE_URL + '/legacy',
        data=json.dumps({
            "version": "1.1",
            "id": 0,
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    result = resp.json()
    assert result['id'] == 0
    assert result['jsonrpc'] == '2.0'
    assert len(result['result']) == 1


def test_sloppy_rpc_conversion():
    """
    Test that a Sloppy-RPC request is still handled ok
    """
    resp = requests.post(
        BASE_URL + '/legacy',
        data=json.dumps({
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    result = resp.json()
    assert result['id'] == '0'
    assert result['jsonrpc'] == '2.0'
    assert len(result['result']) == 1
