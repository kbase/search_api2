import json
import os
import requests
import pytest
from tests.helpers.common import (
    assert_jsonrpc11_result,
    assert_jsonrpc11_error
)
from tests.helpers.integration_setup import (
    do_rpc,
    load_data_file, assert_equal_results
)


def test_search_objects_public(service):
    """A search against public refdata data should succeed"""
    request_test_data = load_data_file('search_objects', 'case-04-request.json')
    response_test_data = load_data_file('search_objects', 'case-04-response.json')
    url = service['app_url'] + '/legacy'
    res = do_rpc(url, request_test_data, response_test_data)
    # Assert characteristics of some properties
    assert res['search_time'] > 0
    assert res['total'] > 0


def test_search_example3(service):
    request_data = load_data_file('search_objects', 'case-06-request.json')
    response_data = load_data_file('search_objects', 'case-06-response.json')
    url = service['app_url'] + '/legacy'
    res = do_rpc(url, request_data, response_data)
    assert res['total'] > 0
    assert res['search_time'] > 0
    assert len(res['objects']) > 0


def test_search_example4(service):
    """Genome features count with no data"""
    request_data = load_data_file('search_objects', 'case-07-request.json')
    response_data = load_data_file('search_objects', 'case-07-response.json')
    url = service['app_url'] + '/legacy'
    res = do_rpc(url, request_data, response_data)
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_example5(service):
    """Genome features search with results"""
    request_data = load_data_file('search_objects', 'case-08-request.json')
    response_data = load_data_file('search_objects', 'case-08-response.json')
    url = service['app_url'] + '/legacy'
    res = do_rpc(url, request_data, response_data)
    assert_equal_results(res, response_data['result'][0])
    assert len(res['objects']) > 0
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_objects_private(service):
    """Search over private data"""
    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('search_objects', 'case-09-request.json')
    response_data = load_data_file('search_objects', 'case-09-response.json')
    url = service['app_url'] + '/legacy'

    res = do_rpc(url, request_data, response_data)

    # TODO: should check more fields.
    assert len(res['objects']) > 0
    for obj in res['objects']:
        assert len(obj['highlight']) > 0


def test_search_objects_multiple_terms_narrow(service):
    """Multiple terms should narrow search results"""
    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    test_data = load_data_file('search_objects', 'case-10.json')
    url = service['app_url'] + '/legacy'
    rpc = test_data['rpc']

    for case in test_data['cases']:
        rpc['params'][0]['match_filter']['full_text_in_all'] = case['full_text_in_all']
        res = do_rpc(url, rpc, {'id': rpc['id']})
        assert res['total'] == case['total']


def test_search_objects_(service):
    """Search for public non-reference data"""
    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    url = service['app_url'] + '/legacy'
    request_data = load_data_file('search_objects', 'case-01-request.json')
    response_data = load_data_file('search_objects', 'case-01-response.json')
    res = do_rpc(url, request_data, response_data)
    assert_equal_results(res, response_data['result'][0])


def test_search_case_01_no_auth(service):
    """Search for public non-reference data, without token"""
    url = service['app_url'] + '/legacy'
    request_data = load_data_file('search_objects', 'case-01-request.json')
    response_data = load_data_file('search_objects', 'case-01-response.json')
    res = do_rpc(url, request_data, response_data)
    assert_equal_results(res, response_data['result'][0])

# Simulates search from data-search with a search term, only private data
# TODO:


# Simulates search from data-search with a search term, only private and public data
# TODO:


def test_search_objects_many_results(service):
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('search_objects', 'case-02-request.json')
    response_data = load_data_file('search_objects', 'case-02-response.json')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    result = assert_jsonrpc11_result(resp.json(), response_data)
    assert result['total'] > 10000


def assert_counts(service, with_private, with_public, expected_count):
    resp = make_call(service, with_private, with_public)
    response_data = load_data_file('search_objects', 'case-03-response.json')
    result = assert_jsonrpc11_result(resp.json(), response_data)
    assert result['total'] == expected_count


def make_call(service, with_private, with_public):
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('search_objects', 'case-03-request.json')
    request_data['params'][0]['access_filter']['with_private'] = with_private
    request_data['params'][0]['access_filter']['with_public'] = with_public

    return requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )


def get_error(service, with_private, with_public):
    resp = make_call(service, with_private, with_public)
    data = resp.json()
    response_data = load_data_file('search_objects', 'case-03-response.json')
    return assert_jsonrpc11_error(data, response_data)


def get_count(service, with_private, with_public):
    resp = make_call(service, with_private, with_public)
    response_data = load_data_file('search_objects', 'case-03-response.json')
    result = assert_jsonrpc11_result(resp.json(), response_data)
    return result['total']

#
# This series of tests relies upon a specific state of data in
# search.


def test_search_objects_private_and_public_counts(service):
    assert_counts(service, 1, 1, 12)


def test_search_objects_private_counts(service):
    assert_counts(service, 1, 0, 5)


def test_search_objects_public_counts(service):
    assert_counts(service, 0, 1, 9)


def test_search_objects_neither_private_nor_public(service):
    error = get_error(service, 0, 0)
    assert error['code'] == -32602
    assert error['message'] == 'Invalid params'


# A safer but less precise method.


def test_search_objects_public_vs_private(service):
    all_count = get_count(service, 1, 1)
    private_count = get_count(service, 1, 0)
    public_count = get_count(service, 0, 1)
    assert private_count < all_count
    assert public_count < all_count
