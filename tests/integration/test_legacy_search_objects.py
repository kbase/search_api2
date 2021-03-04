import json
import os
import requests
import pytest
from src.utils.logger import logger

from tests.helpers.common import (
    assert_jsonrpc20_result
)


def load_data_file(name):
    file_path = os.path.join(os.path.dirname(__file__), 'data/legacy', name)
    logger.info(f'loading data file from "{file_path}"')
    with open(file_path) as f:
        return json.load(f)


def test_search_objects_many_results(service):
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('case-02-request.json')
    response_data = load_data_file('case-02-response.json')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    data = resp.json()
    #  TODO: should be version 1.1 (aka jsonrpc 1.1)
    [result] = assert_jsonrpc20_result(data, response_data)

    assert result['total'] > 10000


def assert_counts(service, with_private, with_public, expected_count):
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('case-03-request.json')
    request_data['params'][0]['access_filter']['with_private'] = with_private
    request_data['params'][0]['access_filter']['with_public'] = with_public

    response_data = load_data_file('case-03-response.json')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    data = resp.json()
    #  TODO: should be version 1.1 (aka jsonrpc 1.1)
    [result] = assert_jsonrpc20_result(data, response_data)

    assert result['total'] == expected_count


def get_count(service, with_private, with_public):
    url = service['app_url'] + '/legacy'

    if 'WS_TOKEN' not in os.environ:
        pytest.skip('Token required for this test')

    request_data = load_data_file('case-03-request.json')
    request_data['params'][0]['access_filter']['with_private'] = with_private
    request_data['params'][0]['access_filter']['with_public'] = with_public

    response_data = load_data_file('case-03-response.json')

    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    data = resp.json()
    #  TODO: should be version 1.1 (aka jsonrpc 1.1)
    [result] = assert_jsonrpc20_result(data, response_data)

    return result['total']

#
# This series of tests relies upon a specific state of data in
# search.


def test_search_objects_private_and_public(service):
    assert_counts(service, 1, 1, 8)


def test_search_objects_private(service):
    assert_counts(service, 1, 0, 2)


def test_search_objects_public(service):
    assert_counts(service, 0, 1, 6)

# A safer but less precise method.


def test_search_objects_public_vs_private(service):
    all_count = get_count(service, 1, 1)
    private_count = get_count(service, 1, 0)
    public_count = get_count(service, 0, 1)
    assert private_count < all_count
    assert public_count < all_count
