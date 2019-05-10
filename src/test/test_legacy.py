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

    def test_count(self):
        """
        Test a valid, vanilla call to the search_objects method
        This should match all documents with:
         - "doc1" in the name
         - is_public is true or access_group is 100
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'SearchAPIThing.search_objects',
                'params': [{
                    "match_filter": {
                        "full_text_in_all": "public",
                        "exclude_subobjects": 1
                    },
                    "pagination": {
                        "start": 0,
                        "count": 10
                    },
                    "post_processing": {
                        "ids_only": 1,
                        "skip_info": 1,
                        "skip_keys": 1,
                        "skip_data": 1,
                        "include_highlight": 1
                    },
                    "access_filter": {
                        "with_private": 1,
                        "with_public": 1
                    }
                }]
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertTrue(resp.ok)
        resp_json = resp.json()
        print('resp', resp_json)
        self.assertEqual(resp_json['total'], 4)
        self.assertEqual(resp_json['pagination'], {'start': 0, 'count': 10})
        self.assertEqual(resp_json['sorting_rules'], [])
        self.assertTrue(resp_json['time'])
        # results = [r['_source'] for r in resp_json['hits']['hits']]
        # self.assertEqual(results, [
        #     {'is_public': True, 'name': 'public-doc1', 'timestamp': 10},
        #     {'is_public': False, 'name': 'private-doc1', 'access_group': 1, 'timestamp': 7}
        # ])
