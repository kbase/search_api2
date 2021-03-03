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
