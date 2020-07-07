import pytest

from src.search1_conversion import convert_params


def test_search_objects_valid():
    params = [{
        'match_filter': {}
    }]
    expected = {
        'query': {'bool': {}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_highlight():
    params = [{
        'match_filter': {},
        'include_highlight': True
    }]
    expected = {
        'query': {'bool': {}},
        'highlight': {'*': {}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_fulltext():
    params = [{
        'match_filter': {'full_text_in_all': 'xyz'},
    }]
    expected = {
        'query': {'bool': {'must': [{'match': {'agg_fields': 'xyz'}}]}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_object_name():
    params = [{
        'match_filter': {'object_name': 'xyz'}
    }]
    expected = {
        'query': {'bool': {'must': [{'match': {'obj_name': 'xyz'}}]}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_timestamp():
    params = [{
        'match_filter': {'timestamp': {'min_date': 0, 'max_date': 1}}
    }]
    expected = {
        'query': {'bool': {'must': [{'range': {'timestamp': {'gte': 0, 'lte': 1}}}]}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_timestamp_invalid():
    with pytest.raises(RuntimeError):
        params = [{
            'match_filter': {'timestamp': {'min_date': 0, 'max_date': 0}}
        }]
        convert_params.search_objects(params)


def test_search_objects_source_tags():
    params = [{
        'match_filter': {'source_tags': ['x', 'y']}
    }]
    expected = {
        'query': {'bool': {'must': [{'term': {'tags': 'x'}}, {'term': {'tags': 'y'}}]}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_source_tags_blacklist():
    params = [{
        'match_filter': {'source_tags': ['x', 'y'], 'source_tags_blacklist': True}
    }]
    expected = {
        'query': {'bool': {'must_not': [{'term': {'tags': 'x'}}, {'term': {'tags': 'y'}}]}},
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_objtypes():
    params = [{
        'object_types': ['x', 'y']
    }]
    expected = {
        'query': {
            'bool': {
                'should': [
                    {'term': {'obj_type_name': 'x'}},
                    {'term': {'obj_type_name': 'y'}}
                ]
            }
        },
        'size': 20, 'from': 0,
        'sort': [], 'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_sorting():
    params = [{
        'sorting_rules': [
            {'property': 'x'},
            {'property': 'timestamp', 'is_object_property': False, 'ascending': False},
        ]
    }]
    expected = {
        'query': {'bool': {}},
        'sort': [{'x': {'order': 'asc'}}, {'timestamp': {'order': 'desc'}}],
        'size': 20, 'from': 0,
        'public_only': False, 'private_only': False
    }
    query = convert_params.search_objects(params)
    print('query', query)
    assert query == expected


def test_search_objects_sorting_invalid_prop():
    with pytest.raises(RuntimeError):
        params = [{
            'sorting_rules': [
                {'property': 'x', 'is_object_property': False, 'ascending': False},
            ]
        }]
        convert_params.search_objects(params)
