import pytest

from src.utils.config import config
from src.search2_conversion import convert_params
from src.exceptions import ResponseError

# TODO Test invalid parameters


def test_search_workspace():
    """Simple test to cover all code paths with a valid result"""
    params = {
        'types': ['KBaseNarrative.Narrative'],
        'include_fields': ['x', 'y'],
        'search': {
            'query': "foo | bar + baz*",
            'fields': ['x', 'y'],
        },
        'sorts': [
            ['x', 'desc'],
            ['y', 'asc']
        ],
        'filters': {
            'operator': 'AND',
            'fields': [
                {
                    'operator': 'OR',
                    'fields': [
                        {'field': 'x', 'range': {'min': 10, 'max': 20}},
                        {'field': 'y', 'not_term': 1}
                    ]
                },
                {'field': 'x', 'term': 1}
            ]
        },
        'paging': {
            'length': 20,
            'offset': 10
        },
        'access': {
            'only_private': True
        },
        'track_total_hits': True
    }
    result = convert_params.search_workspace(params, {})
    expected = {
        'query': {
            'bool': {
                'must': [
                    {
                        'simple_query_string': {
                            'fields': ['x', 'y'],
                            'query': 'foo | bar + baz*',
                            'default_operator': 'AND'
                        }
                    },
                    {
                        'bool': {
                            'must': [
                                {
                                    'bool': {
                                        'should': [
                                            {'range': {'x': {'lte': 20, 'gte': 10}}},
                                            {'bool': {
                                                'must_not': {'term': {'y': {'value': 1}}}
                                            }}
                                        ]
                                    }
                                },
                                {'term': {'x': {'value': 1}}}
                            ]
                        }
                    }
                ]
            }
        },
        'only_public': False,
        'only_private': True,
        'track_total_hits': True,
        'indexes': ['narrative'],
        'from': 10,
        'size': 20,
        'sort': [{
            'x': {'order': 'desc'}
        }, {
            'y': {'order': 'asc'}
        }]
    }
    assert result == expected


def test_search_workspace_invalid_type():
    """Test the case where we have an unknown type name"""
    params = {
        'types': ['xyz'],
    }
    with pytest.raises(ResponseError):
        convert_params.search_workspace(params, {})


def test_search_workspace_blank():
    """Test the case where we generally leave things blank and provide no type names"""
    params = {}
    indexes = list(config['global']['ws_type_to_indexes'].values())
    expected = {
        'query': {'bool': {'must': []}},
        'track_total_hits': False,
        'indexes': indexes,
    }
    result = convert_params.search_workspace(params, {})
    assert result == expected
