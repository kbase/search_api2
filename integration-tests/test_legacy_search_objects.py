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
def test_search_objects_private():
    # So many variations to test...
    params = {
        'match_filter': {
            'full_text_in_all': 'Aquilegia',
            'exclude_subobjects': 1,
            'source_tags': [
                'refdata',
                'noindex'
            ],
            'source_tags_blacklist': 1
        },
        'pagination': {
            'start': 0,
            'size': 20
        },
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
    result = client.search_objects(params)
    # NOTE: sensitive to test data for the user kbasesearchtest1
    assert 'objects' in result, '"objects" not present in result'
    objects = result['objects']
    assert len(objects) == 1, f'result count should be 13, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 1, f'result "total" should be 13, is {result["total"]}'


# @pytest.mark.skip(reason="no way of currently testing this")
def test_search_objects_refdata():
    # So many variations to test...
    params = {
        'match_filter': {
            'full_text_in_all': 'Brachyspira',
            'exclude_subobjects': 1,
            'source_tags': [
                'refdata'
            ],
            'source_tags_blacklist': 0
        },
        'pagination': {
            'start': 0,
            'size': 20
        },
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
    result = client.search_objects(params)
    # NOTE: sensitive to test data for the user kbasesearchtest1
    assert 'objects' in result, '"objects" not present in result'
    objects = result['objects']
    assert len(objects) == 20, f'result count should be 20, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 22, f'result "total" should be 22, is {result["total"]}'

# @pytest.mark.skip(reason="no way of currently testing this")


def test_search_objects_private_all_defaults():
    # So many variations to test...
    # TODO: table testing as is done below
    params = {
        'match_filter': {
            'full_text_in_all': 'rhodobacter',
            'exclude_subobjects': 1,
            'source_tags': [
                'refdata',
                'noindex'
            ],
            'source_tags_blacklist': 1
        },
        'pagination': {
            'start': 0,
            'size': 20
        }
    }
    result = client.search_objects(params)
    # NOTE: sensitive to test data for the user kbasesearchtest1
    assert 'objects' in result, '"objects" not present in result'
    objects = result['objects']
    assert len(objects) == 1, f'result count should be 1, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 1, f'result "total" should be 1, is {result["total"]}'


def test_search_objects_lookupInKeys():
    # So many variations to test...
    paramsBase = {
        'match_filter': {
            'lookupInKeys': {
                'scientific_name': {'value': 'Brachyspira'}
            },
            'exclude_subobjects': 1,
            'source_tags': [
                'refdata'
            ],
            'source_tags_blacklist': 0
        }
    }
    data = [
        {
            'input': {
                'scientific_name': {'value': 'Brachyspira'}
            },
            'expected': {
                'count': 20,
                'total': 22
            }
        },
        {
            'input': {
                'scientific_name': {'value': 'Treponema'}
            },
            'expected': {
                'count': 17,
                'total': 17
            }
        },
        {
            'input': {
                'mean_contig_length': {'int_value': 1139223}
            },
            'expected': {
                'count': 2,
                'total': 2
            }
        },
        {
            'input': {
                'gc_content': {'min_double': 0.50, 'max_double': 0.53}
            },
            'expected': {
                'count': 20,
                'total': 26
            }
        }
    ]
    for datum in data:
        params = paramsBase.copy()
        params['match_filter']['lookupInKeys'] = datum['input']
        expectedCount = datum['expected']['count']
        expectedTotal = datum['expected']['total']

        result = client.search_objects(params)
        # NOTE: sensitive to test data for the user kbasesearchtest1
        assert 'objects' in result, '"objects" not present in result'
        objects = result['objects']
        assert len(objects) == expectedCount, f'result count should be {expectedCount}, is {len(objects)}'
        assert 'total' in result, '"total" not present in result'
        assert result['total'] == expectedTotal, f'result "total" should be {expectedTotal}, is {result["total"]}'
