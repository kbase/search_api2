import json
import pytest
import subprocess
import responses

# For mocking workspace calls
from unittest.mock import patch

from src.utils.config import config
from src.exceptions import UnknownIndex
from src.es_client import search
from src.utils.wait_for_service import wait_for_service
from src.exceptions import ElasticsearchError
from tests.helpers import init_elasticsearch

from tests.helpers.unit_setup import (
    start_service,
    stop_service
)

ES_URL = 'http://localhost:9200'


def setup_module(module):
    start_service(ES_URL, 'Elasticsearch')
    init_elasticsearch()


def teardown_module(module):
    stop_service()


def test_search_public_valid():
    params = {
        'only_public': True,
        'track_total_hits': True,
    }
    result = search(params, {'auth': None})
    assert result['count'] == 4
    assert result['search_time'] >= 0
    assert result['aggregations'] == {}
    expected: set = {
        ('index1', 'public-doc1'),
        ('index2', 'public-doc1'),
        ('index1', 'public-doc2'),
        ('index2', 'public-doc2'),
    }
    docs = {(doc['index'], doc['id']) for doc in result['hits']}
    assert docs == expected


def test_search_query_valid():
    params = {
        'only_public': True,
        'query': {
            "term": {"name": "doc2"},
        },
    }
    result = search(params, {'auth': None})
    assert result['count'] == 2
    assert result['search_time'] >= 0
    assert result['aggregations'] == {}
    expected: set = {
        ('index1', 'public-doc2'),
        ('index2', 'public-doc2'),
    }
    docs = {(doc['index'], doc['id']) for doc in result['hits']}
    assert docs == expected


def test_search_aggs_valid():
    params = {
        'aggs': {'count_by_index': {'terms': {'field': '_index'}}}
    }
    result = search(params, {'auth': None})
    assert result['count'] == 4
    assert result['aggregations']['count_by_index']['counts'] == [
        {'key': 'test_index1', 'count': 2},
        {'key': 'test_index2', 'count': 2},
    ]


def test_search_sort_valid():
    params = {'sort': [{'timestamp': {'order': 'desc'}}, '_score']}
    result = search(params, {'auth': None})
    docs = [r['doc'] for r in result['hits']]
    timestamps = [r['timestamp'] for r in docs]
    assert timestamps == [12, 12, 10, 10]
    # And ascending
    params = {'sort': [{'timestamp': {'order': 'asc'}}, '_score']}
    result = search(params, {'auth': None})
    docs = [r['doc'] for r in result['hits']]
    timestamps = [r['timestamp'] for r in docs]
    assert timestamps == [10, 10, 12, 12]


def test_search_highlight_valid():
    params = {
        'query': {'term': {'name': 'doc1'}},
        'highlight': {'fields': {'name': {}}}
    }
    result = search(params, {'auth': None})
    highlights: set = {hit['highlight']['name'][0] for hit in result['hits']}
    assert highlights == {'public-<em>doc1</em>'}


def test_search_source_filtering_valid():
    params = {
        'source': ['name']
    }
    result = search(params, {'auth': None})
    docs = {json.dumps(r['doc']) for r in result['hits']}
    assert docs == {'{"name": "public-doc1"}', '{"name": "public-doc2"}'}


def test_search_by_index_valid():
    params = {'indexes': ['index1']}
    result = search(params, {'auth': None})
    indexes = {r['index'] for r in result['hits']}
    assert indexes == {'index1'}


def test_search_unknown_index():
    idx_name = 'xyz'
    full_name = config['index_prefix'] + '_' + idx_name
    params = {'indexes': [idx_name]}
    with pytest.raises(UnknownIndex) as ctx:
        search(params, {'auth': None})
    assert str(ctx.value) == f"no such index [{full_name}]"


def test_search_private_valid():
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [1, 2, 3]  # Authorized workspaces
        params = {'only_private': True}
        result = search(params, {'auth': 'x'})
        assert result['count'] == 2
        names = {hit['doc']['name'] for hit in result['hits']}
        assert names == {'private-doc1'}
        is_public = {hit['doc']['is_public'] for hit in result['hits']}
        assert is_public == {False}


def test_search_private_no_access():
    with patch('src.es_client.query.ws_auth') as mocked:
        mocked.return_value = [55]  # Authorized workspaces
        params = {'only_private': True}
        result = search(params, {'auth': 'x'})
        assert result['count'] == 0


@responses.activate
def test_es_response_error():
    """Test the case where ES gives a non-2xx response."""
    prefix = config['index_prefix']
    delim = config['prefix_delimiter']
    index_name_str = prefix + delim + "default_search"
    url = config['elasticsearch_url'] + '/' + index_name_str + '/_search'
    responses.add(responses.POST, url, json={}, status=500)
    with pytest.raises(ElasticsearchError):
        search({}, {'auth': None})


@responses.activate
def test_es_response_error_no_json():
    """Test the case where ES gives a non-2xx response with a non-json body."""
    prefix = config['index_prefix']
    delim = config['prefix_delimiter']
    index_name_str = prefix + delim + "default_search"
    url = config['elasticsearch_url'] + '/' + index_name_str + '/_search'
    responses.add(responses.POST, url, body="!", status=500)
    with pytest.raises(ElasticsearchError):
        search({}, {'auth': None})
