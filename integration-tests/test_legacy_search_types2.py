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
def test_search_types_no_search():
    # So many variations to test...
    params = {
        'match_filter': {
        },
        'access_filter': {
            'with_private': 1,
            'with_public': 0
        }
    }
    result = client.search_types2(params)

    assert 'types' in result, '"types" not present in result'

    # Note: based on data in narratives for kbasesearchtest1 user.
    types = result['types']
    expected = {
        'Genome': 2,
        'Narrative': 1,
        'PairedEndLibrary': 1,
        'SingleEndLibrary': 1
    }
    for type_name, count in expected.items():
        assert type_name in types, f'"{type_name}" not present in types'
        assert types[type_name] == count, f'Count for "{type_name}" should be {count}'


# @pytest.mark.skip(reason="no way of currently testing this")
def test_search_types_rhodobacter():
    # So many variations to test...
    params = {
        'match_filter': {
            'search_term': 'Rhodobacter'
        },
        'access_filter': {
            'with_private': 1,
            'with_public': 0
        }
    }
    result = client.search_types2(params)

    assert 'types' in result, '"types" not present in result'

    # Note: based on data in narratives for kbasesearchtest1 user.
    types = result['types']
    expected = {
        'Genome': 1
    }
    for type_name, count in expected.items():
        assert type_name in types, f'"{type_name}" not present in types'
        assert types[type_name] == count, f'Count for "{type_name}" should be {count}'
