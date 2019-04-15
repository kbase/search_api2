import unittest
import requests
import json

from src.utils.config import init_config

_API_URL = 'http://web:5000'
config = init_config()
_INDEX_NAME = config['index_prefix'] + '.' + 'helloworld'
_TYPE_NAME = 'data'


def _init_elasticsearch():
    """
    Initialize the indexes and documents on elasticsearch before running tests.
    """
    resp = requests.put(
        config['elasticsearch_url'] + '/' + _INDEX_NAME,
        data=json.dumps({
            'settings': {
                'index': {
                    'number_of_shards': 3,
                    'number_of_replicas': 1
                }
            }
        })
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
        url = '/'.join([  # type: ignore
            config['elasticsearch_url'],
            _INDEX_NAME,
            _TYPE_NAME,
            doc['name'],
            '?refresh=wait_for'
        ])
        resp = requests.put(url, data=json.dumps(doc))
        if not resp.ok:
            raise RuntimeError('Error creating doc on ES:', resp.text)


def _tear_down_elasticsearch():
    """
    Drop the elasticsearch index when we exit the tests.
    """
    resp = requests.delete(config['elasticsearch_url'] + '/' + _INDEX_NAME)
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
        self.assertEqual(resp.json(), {'status': 'ok'})

    def test_show_config(self):
        """
        Test the show_config RPC method.
        """
        resp = requests.post(_API_URL, data='{}')
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
            _API_URL,
            data=json.dumps({
                'method': 'search_objects',
                'params': {
                    'indexes': ['HelloWorld'],
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

    def test_search_objects_valid_no_query_no_auth(self):
        """
        Test the search_objects function without providing a query or auth.
        This should return all public docs
        """
        resp = requests.post(
            _API_URL,
            data=json.dumps({
                'method': 'search_objects',
                'params': {
                    'indexes': ['HelloWorld']
                }
            })
        )
        self.assertTrue(resp.ok)
        resp_json = resp.json()
        results = [r['_source'] for r in resp_json['hits']['hits']]
        self.assertEqual(results, [
            {'is_public': True, 'name': 'public-doc1'},
            {'is_public': True, 'name': 'public-doc2'}
        ])
