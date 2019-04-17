import unittest
import requests
import json

from src.utils.config import init_config

_API_URL = 'http://web:5000'
config = init_config()
_TYPE_NAME = 'data'
_INDEX_NAMES = [
    config['index_prefix'] + '.' + 'index1',
    config['index_prefix'] + '.' + 'index2',
]


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
            headers={'Content-Type': 'application/json'}
        )
        if not resp.ok and resp.json()['error']['type'] != 'index_already_exists_exception':
            raise RuntimeError('Error creating index on ES:', resp.text)
    test_docs = [
        # Public doc
        {'name': 'public-doc1', 'is_public': True},
        # Public doc
        {'name': 'public-doc2', 'is_public': True},
        # Private but accessible doc
        {'name': 'private-doc1', 'is_public': False, 'access_group': 28327},
        # Private but inaccessible doc
        {'name': 'private2-doc1', 'is_public': False, 'access_group': 0},
    ]
    for doc in test_docs:
        # Note that the 'refresh=wait_for' option must be set in the URL so we can search on it immediately.
        for i in range(0, 2):  # i will be [0, 1]
            url = '/'.join([  # type: ignore
                config['elasticsearch_url'],
                _INDEX_NAMES[i],
                _TYPE_NAME,
                doc['name'],
                '?refresh=wait_for'
            ])
            resp = requests.put(url, data=json.dumps(doc), headers={'Content-Type': 'application/json'})
            if not resp.ok:
                raise RuntimeError('Error creating doc on ES:', resp.text)


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

    # TODO invalid json response

    def test_status(self):
        resp = requests.get(_API_URL + '/status')
        self.assertEqual(resp.json(), {'status': 'ok'})

    def test_show_config(self):
        """
        Test the show_config RPC method.
        """
        resp = requests.post(_API_URL + '/rpc', data='{}')
        self.assertEqual(resp.json(), {
            'elasticsearch_url': 'http://elasticsearch:9200',
            'workspace_url': 'https://ci.kbase.us/services/ws',
            'index_prefix': 'test'
        })

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
                'params': {
                    'indexes': ['Index1'],
                    'query': {
                        'term': {'name': 'doc1'}
                    }
                }
            }),
            headers={'Authorization': 'F3T2TTJEIBI2Y5HIJYY4MOZ6XLKBVE3B'}
        )
        self.assertTrue(resp.ok)
        resp_json = resp.json()
        results = [r['_source'] for r in resp_json['hits']['hits']]
        self.assertEqual(results, [
            {'is_public': True, 'name': 'public-doc1'},
            {'is_public': False, 'name': 'private-doc1', 'access_group': 28327}
        ])

    def test_count_indexes_valid(self):
        """
        Test the search_objects function, where we aggregate counts by index name.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({
                'method': 'search_objects',
                'params': {'indexes': ['index1', 'index2'], 'count': True}
            })
        )
        self.assertTrue(resp.ok)
        resp_json = resp.json()
        results = resp_json['aggregations']['count_by_index']['buckets']
        self.assertEqual(results, [
            {'key': 'test.index1', 'doc_count': 2},
            {'key': 'test.index2', 'doc_count': 2}
        ])

    def test_show_indexes(self):
        """
        Test the show_indexes function.
        """
        resp = requests.post(
            _API_URL + '/rpc',
            data=json.dumps({'method': 'show_indexes'})
        )
        self.assertTrue(resp.ok)
        resp_json = resp.json()
        names = [r['index'] for r in resp_json]
        self.assertEqual(set(names), {'test.index2', 'test.index1'})
        counts = [int(r['docs.count']) for r in resp_json]
        self.assertEqual(counts, [4, 4])
