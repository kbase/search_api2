import json
import os
import requests
import pytest
from src.utils.logger import logger

from tests.helpers.common import (
    assert_jsonrpc11_result,
    equal
)


def load_data_file(name):
    file_path = os.path.join(os.path.dirname(__file__), 'data/legacy', name)
    logger.info(f'loading data file from "{file_path}"')
    with open(file_path) as f:
        return json.load(f)


def test_search_example1(service):
    request_data = load_data_file('case-04-request.json')
    response_data = load_data_file('case-04-response.json')
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    data = resp.json()
    assert data['version'] == response_data['version']
    assert data['id'] == response_data['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    expected_res = response_data['result'][0]
    assert res['search_time'] > 0
    assert res['total'] > 0
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert res['objects'] == expected_res['objects']


def test_search_example2(service):
    request_data = load_data_file('case-05-request.json')
    response_data = load_data_file('case-05-response.json')
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    data = resp.json()
    assert data['version'] == response_data['version']
    assert data['id'] == response_data['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    assert res['search_time'] > 0
    assert res['type_to_count']  # TODO match more closely when things are more indexed


def test_search_example3(service):
    request_data = load_data_file('case-06-request.json')
    response_data = load_data_file('case-06-response.json')
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    data = resp.json()
    assert data['version'] == response_data['version']
    assert data['id'] == response_data['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    expected_res = response_data['result'][0]
    assert set(res.keys()) == set(expected_res.keys())
    assert res['pagination'] == expected_res['pagination']
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert res['total'] > 0
    assert res['search_time'] > 0
    assert len(res['objects']) > 0


def test_search_example4(service):
    """Genome features count with no data"""
    request_data = load_data_file('case-07-request.json')
    response_data = load_data_file('case-07-response.json')
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    data = resp.json()
    assert data['version'] == response_data['version']
    assert data['id'] == response_data['id']
    assert len(data['result']) == 1
    expected_res = response_data['result'][0]
    res = data['result'][0]
    assert set(res.keys()) == set(expected_res.keys())
    assert res['pagination'] == expected_res['pagination']
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert res['objects'] == expected_res['objects']
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_example5(service):
    """Genome features search with results"""
    request_data = load_data_file('case-08-request.json')
    response_data = load_data_file('case-08-response.json')
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    res = assert_jsonrpc11_result(resp.json(), response_data)
    expected_res = response_data['result'][0]
    assert set(res.keys()) == set(expected_res.keys())
    assert res['pagination'] == expected_res['pagination']
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert len(res['objects']) > 0
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_example6(service):
    """Search example with many options and narrative info."""
    request_data = load_data_file('case-09-request.json')
    response_data = load_data_file('case-09-response.json')
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    res = assert_jsonrpc11_result(resp.json(), response_data)
    assert len(res['objects']) > 0
    for obj in res['objects']:
        assert len(obj['highlight']) > 0


def test_search_example_7(service):
    """Test multiple terms"""
    test_data = load_data_file('case-10.json')
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    rpc = test_data['rpc']

    for case in test_data['cases']:
        rpc['params'][0]['match_filter']['full_text_in_all'] = case['full_text_in_all']
        resp = requests.post(
            url=url,
            headers={'Authorization': os.environ['WS_TOKEN']},
            data=json.dumps(rpc),
        )
        res = assert_jsonrpc11_result(resp.json(), rpc)
        assert res['total'] == case['total']

# This is a normal data-search usage, which returns the
# workspace info and narrative info, for public data.
# Simulates search from data-search with a search term, only public data


def test_search_case_01(service):
    """Search example with many options and narrative info, with token."""
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('case-01-request.json')
    response_data = load_data_file('case-01-response.json')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    data = resp.json()
    assert_jsonrpc11_result(data, response_data)
    [is_equal, path] = equal(data, response_data)
    assert is_equal, path


def test_search_case_01_no_auth(service):
    """Search example with many options and narrative info, without token."""
    url = service['app_url'] + '/legacy'

    request_data = load_data_file('case-01-request.json')
    response_data = load_data_file('case-01-response.json')

    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    data = resp.json()
    assert_jsonrpc11_result(data, response_data)
    [is_equal, path] = equal(data, response_data)
    assert is_equal, path

# Simulates search from data-search with a search term, only private data

# TODO:


# Simulates search from data-search with a search term, only private and public data

# TODO:
