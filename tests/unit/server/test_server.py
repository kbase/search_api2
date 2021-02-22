import json
import requests

from tests.helpers import init_elasticsearch

from tests.helpers.unit_setup import (
    start_service,
    stop_service
)

APP_URL = 'http://localhost:5000'


def setup_module(module):
    start_service(APP_URL, 'searchapi2')
    init_elasticsearch()


def teardown_module(module):
    stop_service()


def test_rpc_valid():
    """Test a basic valid request to /rpc"""
    resp = requests.post(
        APP_URL + '/rpc',
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
        APP_URL + "/legacy",
        headers={"Authorization": "xyz"},
        data=json.dumps({
            # TODO: version 1.1
            "jsonrpc": "2.0",
            "id": "0",
            "method": "KBaseSearchEngine.get_objects",
            "params": [{"guids": ["xyz"]}],
        })
    )
    result = resp.json()
    assert 'error' in result
    assert result['error']['code'] == -32001
    assert resp.status_code == 400
    # print(resp.text)


def test_legacy_valid():
    """Test a basic valid request to /legacy"""
    resp = requests.post(
        APP_URL + '/legacy',
        data=json.dumps({
            # TODO: version 1.1
            "jsonrpc": "2.0",
            "id": 0,
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    # print(json.dumps(resp.json(), indent=4))
    assert resp.status_code == 200
    result = resp.json()
    assert result['id'] == 0
    # TODO: version 1.1
    assert result['jsonrpc'] == '2.0'
    assert 'result' in result
    assert len(result['result']) == 1


def test_rpc_invalid():
    """Test a basic empty request to /rpc"""
    resp = requests.get(APP_URL + '/rpc')
    result = resp.json()
    assert 'error' in result
    assert result['error']['code'] == -32600  # Invalid params


# TODO: should a get request even be accepted?
# The jsonrpc 1.1 "spec" (never actually an accepted spec),
# https://www.jsonrpc.org/historical/json-rpc-1-1-alt.html
# disfavors GET
# Also, KBase clients should not be encouraged to think that GET
# is acceptable.
def test_legacy_invalid():
    """Test a basic empty request to /legacy"""
    resp = requests.get(APP_URL + '/legacy')
    # TODO: should be a 405 - method not allowed
    result = resp.json()
    assert 'error' in result
    assert result['error']['code'] == -32600  # Invalid params

# TODO: actually, I don't think CORS should be set in the service itself,
# rather in the proxy.


def test_handle_options():
    """Handle a cors-style options requests on all paths"""
    paths = ['/', '/rpc', '/status', '/legacy']
    for path in paths:
        resp = requests.options(APP_URL + path)
        assert resp.status_code == 204
        assert resp.text == ''
        assert resp.headers.get('Access-Control-Allow-Origin') == '*'
        assert resp.headers.get('Access-Control-Allow-Methods') == 'POST, GET, OPTIONS'
        assert resp.headers.get('Access-Control-Allow-Headers') == '*'


def test_404():
    resp = requests.get(APP_URL + '/xyz')
    assert resp.status_code == 404
    assert resp.text == ''


def test_legacy_rpc_conversion():
    """
    Test that a JSON-RPC 1.1 request is still handled ok
    """
    resp = requests.post(
        APP_URL + '/legacy',
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
    # TODO: should be version 1.1
    assert result['jsonrpc'] == '2.0'
    assert len(result['result']) == 1


# TODO: why accept non-compliant requests?
def test_sloppy_rpc_conversion():
    """
    Test that a Sloppy-RPC request is still handled ok
    """
    resp = requests.post(
        APP_URL + '/legacy',
        data=json.dumps({
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    result = resp.json()
    # TODO: if no reply sent, should not return?
    assert 'id' in result
    # TODO: should be version 1.1
    assert result['jsonrpc'] == '2.0'
    assert len(result['result']) == 1
