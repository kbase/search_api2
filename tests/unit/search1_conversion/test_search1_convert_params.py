import pytest

from src.search1_conversion import convert_params
from jsonrpc11base.errors import InvalidParamsError


def test_search_objects_valid():
    params = {
        'match_filter': {}
    }
    expected = {
        'query': {'bool': {}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_highlight():
    params = {
        'match_filter': {'full_text_in_all': 'x'},
        'post_processing': {
            'include_highlight': 1
        }
    }
    expected = {
        'query': {
            'bool': {
                'must': [{
                    'match': {
                        'agg_fields': {
                            'query': 'x',
                            'operator': 'AND'
                        }
                    }
                }]
            }
        },
        'highlight': {
            'fields': {'*': {}},
            'highlight_query': {
                'bool': {
                    'must': [{
                        'match': {
                            'agg_fields': {
                                'query': 'x',
                                'operator': 'AND'
                            }
                        }
                    }]
                }
            },
            'require_field_match': False,
        },
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_fulltext():
    params = {
        'match_filter': {'full_text_in_all': 'xyz'},
    }
    expected = {
        'query': {
            'bool': {
                'must': [{
                    'match': {
                        'agg_fields': {
                            'query': 'xyz',
                            'operator': 'AND'
                        }
                    }
                }]
            }
        },
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False,
        'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_object_name():
    params = {
        'match_filter': {'object_name': 'xyz'}
    }
    expected = {
        'query': {'bool': {'must': [{'match': {'obj_name': 'xyz'}}]}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_timestamp():
    params = {
        'match_filter': {'timestamp': {'min_date': 0, 'max_date': 1}}
    }
    expected = {
        'query': {'bool': {'must': [{'range': {'timestamp': {'gte': 0, 'lte': 1}}}]}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_timestamp_invalid():
    with pytest.raises(InvalidParamsError):
        params = {
            'match_filter': {'timestamp': {'min_date': 0, 'max_date': 0}}
        }
        convert_params.search_objects(params)


def test_search_objects_source_tags():
    params = {
        'match_filter': {'source_tags': ['x', 'y']}
    }
    expected = {
        'query': {'bool': {'must': [{'term': {'tags': 'x'}}, {'term': {'tags': 'y'}}]}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_source_tags_blacklist():
    params = {
        'match_filter': {'source_tags': ['x', 'y'], 'source_tags_blacklist': True}
    }
    expected = {
        'query': {'bool': {'must_not': [{'term': {'tags': 'x'}}, {'term': {'tags': 'y'}}]}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_objtypes():
    params = {
        'object_types': ['x', 'y', 'GenomeFeature']
    }
    expected = {
        'query': {
            'bool': {
                'filter': {
                    'bool': {
                        'should': [
                            {'term': {'obj_type_name': 'x'}},
                            {'term': {'obj_type_name': 'y'}}
                        ]
                    }
                }
            }
        },
        'indexes': ['genome_features_2'],
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_sorting():
    params = {
        'sorting_rules': [
            {'property': 'x'},
            {'property': 'timestamp', 'is_object_property': False, 'ascending': False},
        ]
    }
    expected = {
        'query': {'bool': {}},
        'sort': [{'x': {'order': 'asc'}}, {'timestamp': {'order': 'desc'}}],
        'size': 20, 'from': 0,
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_sorting_invalid_prop():
    with pytest.raises(InvalidParamsError):
        params = {
            'sorting_rules': [
                {'property': 'x', 'is_object_property': False, 'ascending': False},
            ]
        }
        convert_params.search_objects(params)


def test_search_objects_lookup_in_keys():
    params = {
        'match_filter': {
            'lookup_in_keys': {
                'x': {'value': 'x'},
                'y': {'min_int': 1, 'max_int': 2},
            }
        },
    }
    expected = {
        'query': {
            'bool': {
                'must': [
                    {'match': {'x': 'x'}},
                    {'range': {'y': {'gte': 1, 'lte': 2}}}
                ]
            }
        },
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_types_valid():
    params = {
        'match_filter': {}
    }
    expected = {
        'query': {'bool': {}},
        'size': 0, 'from': 0,
        'aggs': {'type_count': {'terms': {'field': 'obj_type_name'}}},
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False,
        'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_types(params)
    assert query == expected


def test_get_objects_valid():
    params = {
        'ids': ['x', 'y']
    }
    expected = {
        'query': {'terms': {'_id': ['x', 'y']}}
    }
    query = convert_params.get_objects(params)
    assert query == expected


def test_search_objects_only_public():
    params = {
        'match_filter': {},
        'access_filter': {
            'with_public': 1
        }
    }
    expected = {
        'query': {'bool': {}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': True, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_only_private():
    params = {
        'match_filter': {},
        'access_filter': {
            'with_private': 1
        }
    }
    expected = {
        'query': {'bool': {}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': True,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_private_and_public():
    params = {
        'match_filter': {},
        'access_filter': {
            'with_private': 1,
            'with_public': 1
        }
    }
    expected = {
        'query': {'bool': {}},
        'size': 20, 'from': 0,
        'sort': [{'timestamp': {'order': 'asc'}}],
        'only_public': False, 'only_private': False,
        'track_total_hits': True
    }
    query = convert_params.search_objects(params)
    assert query == expected


def test_search_objects_private_nor_public():
    params = {
        'match_filter': {},
        'access_filter': {
            'with_private': 0,
            'with_public': 0
        }
    }
    with pytest.raises(InvalidParamsError) as re:
        convert_params.search_objects(params)
    assert re.value.code == -32602
    assert re.value.message == 'Invalid params'
    assert re.value.error['message'] == 'May not specify no private data and no public data'
