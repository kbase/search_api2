import json
import os
import requests
import pytest
from src.utils.logger import logger
from tests.integration.legacy_data import (
    search_request1,
    search_response1,
    search_request2,
    search_response2,
    search_request3,
    search_response3,
    search_request4,
    search_response4,
    search_request5,
    search_response5,
    search_request6,
)
from tests.helpers.common import (
    assert_jsonrpc20_result,
    equal
)


def load_data_file(name):
    file_path = os.path.join(os.path.dirname(__file__), 'data/legacy', name)
    logger.info(f'loading data file from "{file_path}"')
    with open(file_path) as f:
        return json.load(f)


def test_search_example1(service):
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(search_request1),
    )
    data = resp.json()
    assert data['jsonrpc'] == search_response1['jsonrpc']
    assert data['id'] == search_response1['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    expected_res = search_response1['result'][0]
    assert res['search_time'] > 0
    assert res['total'] > 0
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert res['objects'] == expected_res['objects']


def test_search_example2(service):
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(search_request2),
    )
    data = resp.json()
    assert data['jsonrpc'] == search_response2['jsonrpc']
    assert data['id'] == search_response2['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    # expected_res = search_response2['result'][0]
    assert res['search_time'] > 0
    assert res['type_to_count']  # TODO match more closely when things are more indexed


def test_search_example3(service):
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(search_request3),
    )
    data = resp.json()
    assert data['jsonrpc'] == search_response3['jsonrpc']
    assert data['id'] == search_response3['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    expected_res = search_response3['result'][0]
    assert set(res.keys()) == set(expected_res.keys())
    assert res['pagination'] == expected_res['pagination']
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert res['total'] > 0
    assert res['search_time'] > 0
    assert len(res['objects']) > 0


def test_search_example4(service):
    """Genome features count with no data"""
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(search_request4),
    )
    data = resp.json()
    assert data['jsonrpc'] == search_response4['jsonrpc']
    assert data['id'] == search_response4['id']
    assert len(data['result']) == 1
    expected_res = search_response4['result'][0]
    res = data['result'][0]
    assert set(res.keys()) == set(expected_res.keys())
    assert res['pagination'] == expected_res['pagination']
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert res['objects'] == expected_res['objects']
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_example5(service):
    """Genome features search with results"""
    url = service['app_url'] + '/legacy'
    resp = requests.post(
        url=url,
        data=json.dumps(search_request5),
    )
    data = resp.json()
    assert data['jsonrpc'] == search_response5['jsonrpc']
    assert data['id'] == search_response5['id']
    assert len(data['result']) == 1
    expected_res = search_response5['result'][0]
    res = data['result'][0]
    assert set(res.keys()) == set(expected_res.keys())
    assert res['pagination'] == expected_res['pagination']
    assert res['sorting_rules'] == expected_res['sorting_rules']
    assert len(res['objects']) > 0
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_example6(service):
    """Search example with many options and narrative info."""
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(search_request6),
    )
    data = resp.json()
    #  TODO: should be version 1.1 (aka jsonrpc 1.1)
    assert data['jsonrpc'] == '2.0'
    assert data['id'] == search_request6['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    assert len(res['objects']) > 0
    for obj in res['objects']:
        assert len(obj['highlight']) > 0

#

# This is a normal data-search usage, which returns the
# workspace info and narrative info, for public data.


# Simulates search from data-search with a search term, only public data


def test_search_case1(service):
    """Search example with many options and narrative info, with token."""
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('case1-request.json')
    response_data = load_data_file('case1-response.json')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    data = resp.json()
    #  TODO: should be version 1.1 (aka jsonrpc 1.1)
    assert_jsonrpc20_result(data, response_data)
    [is_equal, path] = equal(data, response_data)
    assert is_equal, path


def test_search_case1_no_auth(service):
    """Search example with many options and narrative info, without token."""
    url = service['app_url'] + '/legacy'

    request_data = load_data_file('case1-request.json')
    response_data = load_data_file('case1-response.json')

    resp = requests.post(
        url=url,
        data=json.dumps(request_data),
    )
    data = resp.json()
    #  TODO: should be version 1.1 (aka jsonrpc 1.1)
    assert_jsonrpc20_result(data, response_data)
    [is_equal, path] = equal(data, response_data)
    assert is_equal, path

# Simulates search from data-search with a search term, only private data

# TODO:


# Simulates search from data-search with a search term, only private and public data

# TODO:
