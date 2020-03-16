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
def test_search_objects():
    # So many variations to test...
    # TODO: should be just a positive filter on 'narrative'
    params = {
        'match_filter': {
            'search_term': 'Rhodobacter',
            'exclude_subobjects': 1,
            # 'not_tags': [
            #     'refdata',
            #     'noindex'
            # ],
            'tags': [
                'narrative'
            ]
        },

        'offset': 0,
        'limit': 20,
        'post_processing': {
            'ids_only': 0,
            'skip_info': 0,
            'skip_keys': 0,
            'skip_data': 0,
            'include_highlight': 1,
            'add_narrative_info': 1
        },
        'access_filter': {
            'with_private': 1,
            'with_public': 0
        },
        'sorting_rules': [{
            'is_object_property': 0,
            'property': 'access_group_id',
            'ascending': 0
        }]
    }
    result = client.search_objects2(params)
    # NOTE: sensitive to test data for the user kbasesearchtest1
    assert 'objects' in result, '"objects" not present in result'
    objects = result['objects']
    assert len(objects) == 1, f'result count should be 1, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 1, f'result "total" should be 1, is {result["total"]}'


# @pytest.mark.skip(reason="no way of currently testing this")
def test_search_objects_refdata():
    # So many variations to test...
    params = {
        'match_filter': {
            'search_term': 'coli',
            'exclude_subobjects': 1,
            'not_tags': [
                'noindex'
            ],
            'tags': [
                'refdata'
            ]
        },
        'offset': 0,
        'limit': 20,
        'post_processing': {
            'ids_only': 0,
            'skip_info': 0,
            'skip_keys': 0,
            'skip_data': 0,
            'include_highlight': 1,
            'add_narrative_info': 1
        },
        'access_filter': {
            'with_private': 1,
            'with_public': 1
        },
        'sorting_rules': [{
            'is_object_property': 0,
            'property': 'access_group_id',
            'ascending': 0
        }]
    }
    result = client.search_objects2(params)
    # NOTE: sensitive to test data for the user kbasesearchtest1
    assert 'objects' in result, '"objects" not present in result'
    objects = result['objects']
    assert len(objects) == 20, f'result count should be 20, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 520, f'result "total" should be 520, is {result["total"]}'
