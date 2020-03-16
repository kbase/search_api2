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
            'full_text_in_all': 'coli',
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
    assert len(objects) == 13, f'result count should be 13, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 13, f'result "total" should be 13, is {result["total"]}'


# @pytest.mark.skip(reason="no way of currently testing this")
def test_search_objects_refdata():
    # So many variations to test...
    params = {
        'match_filter': {
            'full_text_in_all': 'coli',
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
    assert result['total'] == 520, f'result "total" should be 520, is {result["total"]}'

# @pytest.mark.skip(reason="no way of currently testing this")


def test_search_objects_private_all_defaults():
    # So many variations to test...
    params = {
        'match_filter': {
            'full_text_in_all': 'coli',
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
    assert len(objects) == 13, f'result count should be 13, is {len(objects)}'
    assert 'total' in result, '"total" not present in result'
    assert result['total'] == 13, f'result "total" should be 13, is {result["total"]}'


def test_search_objects_lookupInKeys():
    # So many variations to test...
    paramsBase = {
        'match_filter': {
            'lookupInKeys': {
                'scientific_name': {'value': 'rhodobacter'}
            },
            'exclude_subobjects': 1,
            'source_tags': [
                'refdata'
            ],
            'source_tags_blacklist': 1
        }
    }
    data = [
        {
            'input': {
                'scientific_name': {'value': 'rhodobacter'}
            },
            'expected': {
                'count': 18,
                'total': 18
            }
        },
        {
            'input': {
                'scientific_name': {'value': 'coli'}
            },
            'expected': {
                'count': 11,
                'total': 11
            }
        },
        {
            'input': {
                'mean_contig_length': {'int_value': 4639221}
            },
            'expected': {
                'count': 2,
                'total': 2
            }
        },
        {
            'input': {
                'gc_content': {'min_double': 0.507, 'max_double': 0.508}
            },
            'expected': {
                'count': 6,
                'total': 6
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
