import json
import requests

# TODO: Remove this test file - it  is actually an integration test;
# code exercised here will NOT be detected by coverage.


def test_rpc_valid(services):
    """Test a basic valid request to /rpc"""
    resp = requests.post(
        services['app_url'] + '/rpc',
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


def test_get_auth_auth_fail_resp(services):
    resp = requests.post(
        services['app_url'] + "/legacy",
        headers={"Authorization": "xyz"},
        data=json.dumps({
            "version": "1.1",
            "method": "KBaseSearchEngine.get_objects",
            "params": [{"guids": ["xyz"]}],
        })
    )
    result = resp.json()
    assert result['version'] == '1.1'
    assert 'error' in result
    error = result['error']
    assert error['code'] == -32001
    assert error['message'] == 'Auth error'
    assert error['name'] == 'JSONRPCError'


def test_search_objects_auth_fail_resp(services):
    resp = requests.post(
        services['app_url'] + "/legacy",
        headers={"Authorization": "xyz"},
        data=json.dumps({
            "version": "1.1",
            "id": "0",
            "method": "KBaseSearchEngine.search_objects",
            "params": [{"guids": ["xyz"]}],
        })
    )
    result = resp.json()
    assert result['version'] == '1.1'
    assert 'error' in result
    error = result['error']
    assert error['code'] == -32001
    assert error['message'] == 'Auth error'
    assert error['name'] == 'JSONRPCError'


def test_search_types_auth_fail_resp(services):
    resp = requests.post(
        services['app_url'] + "/legacy",
        headers={"Authorization": "xyz"},
        data=json.dumps({
            "version": "1.1",
            "id": "0",
            "method": "KBaseSearchEngine.search_types",
            "params": [{"guids": ["xyz"]}],
        })
    )
    result = resp.json()
    assert result['version'] == '1.1'
    assert 'error' in result
    error = result['error']
    assert error['code'] == -32001
    assert error['message'] == 'Auth error'
    assert error['name'] == 'JSONRPCError'


def test_legacy_valid(services):
    """Test a basic valid request to /legacy"""
    resp = requests.post(
        services['app_url'] + '/legacy',
        data=json.dumps({
            "version": "1.1",
            "id": 0,
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result['id'] == 0
    assert result['version'] == '1.1'
    assert 'result' in result
    assert len(result['result']) == 1


def test_rpc_invalid(services):
    """Test a basic empty request to /rpc"""
    resp = requests.get(services['app_url'] + '/rpc')
    result = resp.json()
    assert 'error' in result
    assert result['error']['code'] == -32600  # Invalid params


# TODO: should a get request even be accepted?
# The jsonrpc 1.1 "spec" (never actually an accepted spec),
# https://www.jsonrpc.org/historical/json-rpc-1-1-alt.html
# disfavors GET
# Also, KBase clients should not be encouraged to think that GET
# is acceptable.
def test_legacy_invalid_method(services):
    """Test a basic empty request to /legacy"""
    resp = requests.get(services['app_url'] + '/legacy')
    assert resp.status_code == 405
    resp = requests.delete(services['app_url'] + '/legacy')
    assert resp.status_code == 405
    resp = requests.patch(services['app_url'] + '/legacy')
    assert resp.status_code == 405
    resp = requests.head(services['app_url'] + '/legacy')
    assert resp.status_code == 405
    resp = requests.put(services['app_url'] + '/legacy')
    assert resp.status_code == 405


# TODO: actually, I don't think CORS should be set in the service itself,
# rather in the proxy.


def test_handle_options(services):
    """Handle a cors-style options requests on all paths"""
    paths = ['/', '/rpc', '/status', '/legacy']
    for path in paths:
        resp = requests.options(services['app_url'] + path)
        assert resp.status_code == 204
        assert resp.text == ''
        assert resp.headers.get('Access-Control-Allow-Origin') == '*'
        assert resp.headers.get('Access-Control-Allow-Methods') == 'POST, GET, OPTIONS'
        assert resp.headers.get('Access-Control-Allow-Headers') == '*'


def test_404(services):
    resp = requests.get(services['app_url'] + '/xyz')
    assert resp.status_code == 404
    assert resp.text == ''


def test_legacy_rpc_conversion(services):
    """
    Test that a JSON-RPC 1.1 request is still handled ok
    """
    resp = requests.post(
        services['app_url'] + '/legacy',
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
    assert result['version'] == '1.1'
    assert len(result['result']) == 1


# TODO: why accept non-compliant requests?
def test_sloppy_rpc_conversion(services):
    """
    Test that a Sloppy-RPC request is still handled ok
    """
    resp = requests.post(
        services['app_url'] + '/legacy',
        data=json.dumps({
            "method": "KBaseSearchEngine.get_objects",
            "params": [{
                "guids": ['xyz']
            }]
        })
    )
    result = resp.json()
    assert result['version'] == '1.1'
    assert len(result['result']) == 1
