import json
import os
import requests

from tests.helpers.integration_setup import setup
from src.utils.wait_for_service import wait_for_service
from tests.integration.data import (
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


APP_URL = os.environ.get("APP_URL", 'http://localhost:5000')

setup()
# This implicitly tests the "/" path
wait_for_service(APP_URL, "search2")


def test_search_example1():
    url = APP_URL + '/legacy'
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


def test_search_example2():
    url = APP_URL + '/legacy'
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


def test_search_example3():
    url = APP_URL + '/legacy'
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
    # TODO assert on access_group_narrative_info
    # assert ['access_group_narrative_info']


def test_search_example4():
    """Genome features count with no data"""
    url = APP_URL + '/legacy'
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


def test_search_example5():
    """Genome features search with results"""
    url = APP_URL + '/legacy'
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
    assert len(res['objects_info']) > 0
    assert res['total'] > 0
    assert res['search_time'] > 0


def test_search_example6():
    """Search example with many options and narrative info."""
    url = APP_URL + '/legacy'
    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(search_request6),
    )
    data = resp.json()
    assert data['jsonrpc'] == '2.0'
    assert data['id'] == search_request6['id']
    assert len(data['result']) == 1
    res = data['result'][0]
    assert len(res['objects']) > 0
    assert len(res['objects_info']) > 0
    for obj in res['objects']:
        assert len(obj['highlight']) > 0
