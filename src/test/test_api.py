import unittest
import requests
import json
import yaml
import jsonschema

from src.utils.config import init_config

_API_URL = 'http://localhost:5000'
config = init_config()
_INDEX_NAMES = [
    config['index_prefix'] + '.index1',
    config['index_prefix'] + '.index2',
]
_SCHEMAS_PATH = 'src/server/method_schemas.yaml'
with open(_SCHEMAS_PATH) as fd:
    _SCHEMAS = yaml.safe_load(fd)


def _init_elasticsearch():
    """
    Initialize the indexes and documents on elasticsearch before running tests.
    """
    for index_name in _INDEX_NAMES:
        resp = requests.put(
            config['elasticsearch_url'] + '/' + index_name,
            data=json.dumps({
                'settings': {
                    'index': {'number_of_shards': 3, 'number_of_replicas': 1}
                }
            }),
            headers={'Content-Type': 'application/json'},
        )
        if not resp.ok and resp.json()['error']['type'] != 'index_already_exists_exception':
            raise RuntimeError('Error creating index on ES:', resp.text)
    test_docs = [
        # Public doc
        {'name': 'public-doc1', 'is_public': True, 'timestamp': 10},
        # Public doc
        {'name': 'public-doc2', 'is_public': True, 'timestamp': 12},
        # Private but accessible doc
        {'name': 'private-doc1', 'is_public': False, 'access_group': 1, 'timestamp': 7},
        # Private but inaccessible doc
        {'name': 'private2-doc1', 'is_public': False, 'access_group': 99, 'timestamp': 9},
    ]
    for doc in test_docs:
        # Note that the 'refresh=wait_for' option must be set in the URL so we can search on it immediately.
        for i in range(0, 2):  # i will be [0, 1]
            url = '/'.join([  # type: ignore
                config['elasticsearch_url'],
                _INDEX_NAMES[i],
                '_doc',
                doc['name'],
                '?refresh=wait_for'
            ])
            resp = requests.put(url, data=json.dumps(doc), headers={'Content-Type': 'application/json'})
            if not resp.ok:
                raise RuntimeError('Error creating doc on ES:', resp.text)

    # create default_search alias for all fields.
    url = '/'.join([
        config['elasticsearch_url'],
        '_aliases'
    ])
    body = {
        "actions": [{"add": {"indices": _INDEX_NAMES, "alias": config['index_prefix'] + ".default_search"}}]
    }
    resp = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
    if not resp.ok:
        raise RuntimeError("Error creating aliases on ES:", resp.text)


def _tear_down_elasticsearch():
    """
    Drop the elasticsearch index when we exit the tests.
    """
    for index_name in _INDEX_NAMES:
        resp = requests.delete(config['elasticsearch_url'] + '/' + index_name)
        if not resp.ok:
            print('Error tearing down ES index:', resp.text)


class TestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _init_elasticsearch()

    @classmethod
    def tearDownClass(cls):
        _tear_down_elasticsearch()

    def test_status(self):
        resp = requests.get(_API_URL + '/status')
        self.assertEqual(resp.text, '')

    def test_show_config(self):
        """
        Test the show_config RPC method.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'method': 'show_config',
                'id': 0,
                'jsonrpc': '2.0',
            })
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        self.assertTrue(resp.json())

    def test_search_objects_valid(self):
        """
        Test a valid, vanilla call to the search_objects method
        This should match all documents with:
         - "doc1" in the name
         - is_public is true or access_group is 100
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'method': 'search_objects',
                'id': 0,
                'jsonrpc': '2.0',
                'params': {
                    'indexes': ['Index1'],
                    'query': {
                        'term': {'name': 'doc1'}
                    }
                }
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        resp_json = resp.json()
        result = resp_json['result']
        results = [r['doc'] for r in result['hits']]
        self.assertEqual(results, [
            {'is_public': True, 'name': 'public-doc1', 'timestamp': 10},
            {'is_public': False, 'name': 'private-doc1', 'access_group': 1, 'timestamp': 7}
        ])
        jsonschema.validate(result, _SCHEMAS['search_objects']['result'])

    def test_count_valid(self):
        """
        Test the search_objects function, where we aggregate counts by index name.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'method': 'search_objects',
                'id': 0,
                'jsonrpc': '2.0',
                'params': {
                    'indexes': ['index1', 'index2'],
                    'aggs': {
                        'count_by_index': {'terms': {'field': '_index'}}
                    }
                }
            })
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        resp_json = resp.json()
        result = resp_json['result']
        results = result['aggregations']['count_by_index']['counts']
        self.assertEqual(results, [
            {'key': 'test.index1', 'count': 2},
            {'key': 'test.index2', 'count': 2}
        ])
        jsonschema.validate(result, _SCHEMAS['search_objects']['result'])

    def test_show_indexes(self):
        """
        Test the show_indexes function.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({'jsonrpc': '2.0', 'id': 0, 'method': 'show_indexes'})
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        resp_json = resp.json()
        result = resp_json['result']
        names = [r['name'] for r in result]
        self.assertEqual(set(names), {'index2', 'index1'})
        counts = [int(r['count']) for r in result]
        self.assertEqual(counts, [4, 4])
        jsonschema.validate(result, _SCHEMAS['show_indexes']['result'])

    def test_custom_sort(self):
        """
        Test the search_objects function with a sort
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'jsonrpc': '2.0',
                'id': 0,
                'method': 'search_objects',
                'params': {
                    'indexes': ['index1', 'index2'],
                    'query': {'term': {'name': 'doc1'}},
                    'sort': [
                        {'timestamp': {'order': 'desc'}},
                        '_score'
                    ]
                }
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        resp_json = resp.json()
        result = resp_json['result']
        docs = [r['doc'] for r in result['hits']]
        timestamps = [r['timestamp'] for r in docs]
        self.assertEqual(timestamps, [10, 10, 7, 7])

    def test_track_total_hits(self):
        """
        Test the elasticsearch track total hits feature.
        TODO: figure out what to assert.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'jsonrpc': '2.0',
                'id': 0,
                'method': 'search_objects',
                'params': {
                    'indexes': ['index1', 'index2'],
                    'query': {'term': {'name': 'doc1'}},
                    'track_total_hits': True
                }
            })
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        # resp_json = resp.json()
        # result = resp_json['result']

    def test_highlights(self):
        """
        Test the elasticsearch result highlighting feature.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'jsonrpc': '2.0',
                'id': 0,
                'method': 'search_objects',
                'params': {
                    'indexes': ['index1', 'index2'],
                    'query': {'term': {'name': 'doc1'}},
                    'highlight': {'name': {}}
                }
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertTrue(resp.ok, msg=f"response: {resp.text}")
        resp_json = resp.json()
        result = resp_json['result']
        highlights = {hit['highlight']['name'][0] for hit in result['hits']}
        self.assertEqual(highlights, {'public-<em>doc1</em>', 'private-<em>doc1</em>'})

    def test_invalid_json(self):
        """
        Test a request body with invalid JSON syntax.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data='!hi!'
        )
        resp_json = resp.json()
        self.assertEqual(resp_json['id'], None)
        self.assertEqual(resp_json['error']['code'], -32700)
        self.assertEqual(resp_json['error']['message'], 'Parse error')
