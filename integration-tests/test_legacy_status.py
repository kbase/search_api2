from clients.searchapi_client import SearchAPILegacy
import os
# import pytest

TOKEN = os.environ.get("TOKEN")
if TOKEN is None:
    print('TOKEN environment variable is required')
    exit(1)

URL = os.environ.get("URL")
if URL is None:
    print('URL environment variable is required')
    exit(1)

client = SearchAPILegacy(TOKEN, URL)


# @pytest.mark.skip(reason="no way of currently testing this")
def test_status():
    status = client.status()
    assert 'state' in status, 'state key not present'
    assert status['state'] == 'OK', 'state key not OK'
    assert 'version' in status, 'version key not present'
    assert 'message' in status, 'message key not present'
    assert status['message'] == '', 'message value not correct, should be empty string'
    assert 'git_url' in status, 'git_url key not present'
    assert 'git_commit_hash' in status, 'git_commit_hash not preset'
