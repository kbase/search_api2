from src.search2_conversion import convert_params

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
        "query": {
            "simple_query_string": {
                "fields": ["x", "y"],
                "query": "foo | bar + baz*"
            },
            "bool": {
                "must": [
                    {
                        "should": [
                            {"range": {"x": {"lte": 20, "gte": 10}}},
                            {"must_not": {"term": {"y": {"value": 1}}}}
                        ]
                    },
                    {
                        "term": {"x": {"value": 1}}
                    }
                ]
            }
        },
        "only_public": False,
        "only_private": True,
        "track_total_hits": True,
        "sort": [
            {"x": {"order": "desc"}},
            {"y": {"order": "asc"}}
        ]
    }
    assert result == expected
