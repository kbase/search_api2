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
def test_list_types():
    types = client.list_types()
    # This call is not implemented for real; probably never will be.
    # We should have a similar call, though, which exposes information about the
    # configuration of and capabilities of supported types or whether a type is
    # blacklisted or existing in the workspace but not supported.
    assert types == {}, 'should return an empty dict'
