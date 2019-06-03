import unittest
import requests
import json

from src.utils.config import init_config

_API_URL = 'http://web:5000'
_CONFIG = init_config()
_TYPE_NAME = 'data'  # TODO pull this out of global config
_INDEX_NAMES = [
    _CONFIG['index_prefix'] + '.' + 'index1',
    _CONFIG['index_prefix'] + '.' + 'index2',
    _CONFIG['index_prefix'] + '.' + 'narrative',
    *[_CONFIG['index_prefix'] + '.' + name for name in _CONFIG['global']['ws_subobjects']]
]


class TestLegacy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _init_elasticsearch()

    @classmethod
    def tearDownClass(cls):
        _tear_down_elasticsearch()

    def test_basic_text_search(self):
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
                        "with_private": 0,
                        "with_public": 1
                    }
                }]
            })
        )
        self.assertTrue(resp.ok)
        resp_json = resp.json()
        self.assertEqual(resp_json['total'], 4)
        self.assertEqual(resp_json['pagination'], {'start': 0, 'count': 10})
        self.assertEqual(resp_json['sorting_rules'], [])
        self.assertTrue('search_time' in resp_json)
        self.assertEqual(len(resp_json['objects']), 4)

    def test_get_objects(self):
        """
        Test the legacy/get_objects method using a list of guids
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchAPI.get_objects',
                'params': [{
                    'guids': ['public-doc1', 'public-doc2']
                }]
            })
        )
        self.assertEqual(len(resp.json()['objects']), 4)

    def test_match_value_structure(self):
        """
        Test the per-keyword filtering and the MatchValue type in the original API.
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchAPI.search_objects',
                'params': [{
                    'match_filter': {
                        'lookupInKeys': {'access_group': {'value': 1}}
                    },
                    'access_filter': {
                        'with_private': 0,
                        'with_public': 1
                    }
                }]
            })
        )
        # Count of 2 for public-doc1 in both indexes
        # Plus 1 more for the genome feature doc
        self.assertEqual(len(resp.json()['objects']), 3)

    def test_match_value_range(self):
            """
            Test the per-keyword filtering and the MatchValue type in the original API.
            """
            resp = requests.post(
                _API_URL + '/legacy',
                data=json.dumps({
                    'method': 'KBaseSearchAPI.search_objects',
                    'params': [{
                        'match_filter': {
                            'lookupInKeys': {
                                'timestamp': {'min_int': 7, 'max_int': 10}
                            }
                        },
                        'access_filter': {
                            'with_private': 1,
                            'with_public': 1
                        }
                    }]
                }),
                headers={'Authorization': 'valid_token'}
            )
            print('resp', resp.json())
            # 2 for private-doc1 in both indexes, plus 2 for public-doc1 in both indexes
            self.assertEqual(len(resp.json()['objects']), 4)
            resp2 = requests.post(
                _API_URL + '/legacy',
                data=json.dumps({
                    'method': 'KBaseSearchAPI.search_objects',
                    'params': [{
                        'match_filter': {
                            'lookupInKeys': {
                                'timestamp': {'min_int': 7, 'max_int': 12},
                            }
                        },
                        'access_filter': {
                            'with_private': 1,
                            'with_public': 1
                        }
                    }]
                }),
                headers={'Authorization': 'valid_token'}
            )
            print('resp2', resp2.json())
            self.assertEqual(len(resp2.json()['objects']), 6)

    def test_exclude_subobjects(self):
        """
        Test that the `exclude_subobjects` parameter excludes the genome
        feature test document created in _init_elasticsearch
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchAPI.search_objects',
                'params': [{
                    'match_filter': {
                        'full_text_in_all': 'featurexyz',
                        # 'lookupInKeys': {'name': {'value': 'featurexyz'}},
                        'exclude_subobjects': 0
                    },
                    'access_filter': {
                        'with_private': 1,
                        'with_public': 1
                    }
                }]
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertEqual(len(resp.json()['objects']), 1)
        resp2 = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchAPI.search_objects',
                'params': [{
                    'match_filter': {
                        'full_text_in_all': 'featurexyz',
                        # 'lookupInKeys': {'name': {'value': 'featurexyz'}},
                        'exclude_subobjects': 1
                    },
                    'access_filter': {
                        'with_private': 1,
                        'with_public': 1
                    }
                }]
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertEqual(len(resp2.json()['objects']), 0)


def _init_elasticsearch():
    """
    Initialize the indexes and documents on elasticsearch before running tests.
    """
    for index_name in _INDEX_NAMES:
        resp = requests.put(
            _CONFIG['elasticsearch_url'] + '/' + index_name,
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
        {'name': 'public-doc1', 'is_public': True, 'timestamp': 10, 'access_group': 1},
        # Public doc
        {'name': 'public-doc2', 'is_public': True, 'timestamp': 12, 'access_group': 2},
        # Private but accessible doc
        {'name': 'private-doc1', 'is_public': False, 'access_group': 1, 'timestamp': 7},
        # Private but inaccessible doc
        {'name': 'private2-doc1', 'is_public': False, 'access_group': 99, 'timestamp': 9}
    ]
    for doc in test_docs:
        # Note that the 'refresh=wait_for' option must be set in the URL so we can search on it immediately.
        for i in range(0, 2):  # i will be [0, 1]
            url = '/'.join([  # type: ignore
                _CONFIG['elasticsearch_url'],
                _INDEX_NAMES[i],
                _TYPE_NAME,
                doc['name'],
                '?refresh=wait_for'
            ])
            resp = requests.put(url, data=json.dumps(doc), headers={'Content-Type': 'application/json'})
            if not resp.ok:
                raise RuntimeError('Error creating doc on ES:', resp.text)
    # Create a special test index that is considered a workspace "subobject" by the global config
    # This way we can test the `exclude_subobjects` option.
    subobj_idx_name = _CONFIG['index_prefix'] + '.' + _CONFIG['global']['ws_subobjects'][0]
    subobj_doc = {
        'name': 'featurexyz',
        'is_public': True,
        'access_group': 1,
        'timestamp': 15
    }
    url = '/'.join([
        _CONFIG['elasticsearch_url'],
        subobj_idx_name,
        _TYPE_NAME,
        'featurexyz',
        '?refresh=wait_for'
    ])
    resp = requests.put(url, data=json.dumps(subobj_doc), headers={'Content-Type': 'application/json'})
    if not resp.ok:
        raise RuntimeError('Error creating doc on ES:', resp.text)


def _tear_down_elasticsearch():
    """
    Drop the elasticsearch index when we exit the tests.
    """
    for index_name in _INDEX_NAMES:
        resp = requests.delete(_CONFIG['elasticsearch_url'] + '/' + index_name)
        if not resp.ok:
            print('Error tearing down ES index:', resp.text)
