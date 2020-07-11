import json
import os
import requests
import subprocess

from src.utils.wait_for_service import wait_for_service
from tests.integration.test_data import (
    search_request1,
    search_response1,
    search_request2,
    search_response2,
)


APP_URL = 'http://localhost:5000'
ES_URL = os.environ.get("ES_URL", "http://localhost:9500")
# TOKEN = os.environ["TOKEN"]
INDEX_PREFIX = os.environ.get('INDEX_PREFIX', 'search2')
USER_PROFILE_URL = os.environ.get('USER_PROFILE_URL', 'https://ci.kbase.us/services/user_profile')
WS_URL = os.environ.get('WS_URL', 'https://ci.kbase.us/services/ws')
IMAGE_NAME = "kbase/search2"

# Start the services
# This implicitly tests the "/" path
cmd = f"""
docker build . -t {IMAGE_NAME} && \\
docker run -e ELASTICSEARCH_URL={ES_URL} \\
           -e WORKSPACE_URL={WS_URL} \\
           -e USER_PROFILE_URL={USER_PROFILE_URL} \\
           -e WORKERS=2 \\
           -e INDEX_PREFIX={INDEX_PREFIX} \\
           -e INDEX_PREFIX_DELIMITER=. \\
           --network host \\
           {IMAGE_NAME}
"""
print(f'Running command:\n{cmd}')
subprocess.Popen(cmd, shell=True)
wait_for_service(APP_URL, "search2")


# TODO old api seems to have default sort on timestamp -- do we want this?


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
