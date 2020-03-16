import unittest
import requests
import json

from src.utils.config import init_config

_API_URL = 'http://localhost:5000'
_CONFIG = init_config()
# TODO: we need aliases too. E.g. obj_types is translated from KBase workspace type names
# (note w/o module name prefix) to index alias (the original implementation here was just
# a filter on the type field, which doesn't work when sorting too).
_INDEX_NAMES = [
    _CONFIG['index_prefix'] + '.index_1',
    _CONFIG['index_prefix'] + '.index_2',
    _CONFIG['index_prefix'] + '.genome',  # since there are no aliases, we use the plain index name
    _CONFIG['index_prefix'] + '.genome_feature',
    _CONFIG['index_prefix'] + '.narrative',
    *[_CONFIG['index_prefix'] + '.' + name for name in _CONFIG['global']['ws_subobjects']]
]

_NON_SUB_NAMES = [
    _CONFIG['index_prefix'] + '.index_1',
    _CONFIG['index_prefix'] + '.index_2',
    _CONFIG['index_prefix'] + '.narrative'
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
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
                'params': [{
                    "match_filter": {
                        "full_text_in_all": "public",
                        'exclude_subobjects': 1
                    },
                    'pagination': {
                        'start': 0,
                        'count': 20,
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
            }),
            headers={'Authorization': 'valid_token'}
        )
        try:
            resp_json = resp.json()
            result = resp_json['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertTrue(resp.ok)
        self.assertEqual(result['total'], 4)
        self.assertEqual(result['pagination'], {'start': 0, 'count': 10})
        self.assertEqual(result['sorting_rules'], [])
        self.assertTrue('search_time' in result)
        self.assertEqual(len(result['objects']), 4)
        objects = result['objects']
        names = {obj['object_name'] for obj in objects}
        self.assertEqual(names, {'public-doc1', 'public-doc2'})

    def test_get_objects(self):
        """
        Test the legacy/get_objects method using a list of guids
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.get_objects',
                'version': '1.1',
                'id': '12345',
                'params': [{
                    'guids': ['public-doc1', 'public-doc2']
                }]
            }),
            headers={'Authorization': 'valid_token'}
        )
        try:
            results = resp.json()['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertEqual(len(results['objects']), 4)

    def test_match_value_structure(self):
        """
        Test the per-keyword filtering and the MatchValue type in the original API.
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
                'params': [{
                    'match_filter': {
                        'lookupInKeys': {'access_group': {'int_value': 1}}
                    },
                    'access_filter': {
                        'with_private': 0,
                        'with_public': 1
                    }
                }]
            }),
            headers={'Authorization': 'valid_token'}
        )
        # Count of 2 for public-doc1 in both indexes
        # Excludes the genome feature doc by default
        try:
            result = resp.json()['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertEqual(len(result['objects']), 2, msg=f"contents of result = {result}")

    def test_match_value_range(self):
        """
        Test the per-keyword filtering and the MatchValue type in the original API.
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
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
        # 2 for private-doc1 in both indexes, plus 2 for public-doc1 in both indexes
        try:
            result = resp.json()['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertEqual(len(result['objects']), 4)
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
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
        try:
            result = resp.json()['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertEqual(len(result['objects']), 6)

    def test_search_subobjects(self):
        """
        Test that the `exclude_subobjects` parameter excludes the genome
        feature test document created in _init_elasticsearch
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
                'params': [{
                    'object_types': ['GenomeFeature'],
                    'match_filter': {
                        'lookupInKeys': {'name': {'value': 'featurexyz'}},
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
        try:
            result = resp.json()['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertEqual(len(result['objects']), 1, msg=f"contents of result: {result}")
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
                'params': [{
                    'match_filter': {
                        'lookupInKeys': {'obj_name': {'value': 'featurexyz'}},
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
        respj = resp.json()
        if 'error' in respj:
            raise RuntimeError(json.dumps(respj))
        result = respj['result'][0]
        self.assertEqual(len(result['objects']), 0, msg=f"contents of result = {result}")

    def test_search_types(self):
        """
        Test the `search_types` method which takes a match_filter and
        access_filter and returns a count of each object type.
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'version': '1.1',
                'id': '12345',
                'method': 'KBaseSearchEngine.search_types',
                'params': [{'match_filter': {}}]
            }),
            headers={'Authorization': 'valid_token'}
        )
        try:
            result = resp.json()['result'][0]
        except Exception:
            raise RuntimeError(resp.text)
        self.assertTrue('search_time' in result)
        self.assertEqual(result['type_to_count'], {'Typea': 4, 'Typeb': 2})

    def test_narrative_example(self):
        """
        Test a real example request from the narrative side-panel
        """
        resp = requests.post(
            _API_URL + '/legacy',
            data=json.dumps({
                'method': 'KBaseSearchEngine.search_objects',
                'version': '1.1',
                'id': '12345',
                'params': [{
                    'object_types': ['Genome'],
                    'match_filter': {
                        'full_text_in_all': 's',
                        'exclude_subobjects': 1,
                        'source_tags': ['refdata'],
                        'source_tags_blacklist': 0,
                        'lookupInKeys': {
                            'source': {'string_value': 'refseq'},
                        }
                    },
                    'pagination': {
                        'start': 0,
                        'count': 20
                    },
                    'post_processing': {
                        'ids_only': 0, 'skip_info': 0, 'skip_keys': 0, 'skip_data': 0, 'include_highlight': 0
                    },
                    'access_filter': {
                        'with_private': 0, 'with_public': 1
                    },
                    'sorting_rules': [{
                        'is_object_property': 1, 'property': 'scientific_name', 'ascending': 1
                    }]
                }]
            }),
            headers={'Authorization': 'valid_token'}
        )
        self.assertTrue(resp.ok, msg=f"resp: {resp.text}")
        resp_json = resp.json()

        self.assertEqual(resp_json['result'][0]['total'], 0)


def _init_elasticsearch():
    """
    Initialize the indexes and documents on elasticsearch before running tests.
    """
    for index_name in _INDEX_NAMES:
        test_mapping = {
            'agg_fields': {'type': 'text'},
            'obj_name': {'type': 'keyword', 'copy_to': 'agg_fields'},
            'is_public': {'type': 'boolean'},
            'timestamp': {'type': 'integer'},
            'access_group': {'type': 'integer'},
            'obj_type_name': {'type': 'keyword', 'copy_to': 'agg_fields'},
            'scientific_name': {
                'type': 'text',
                'copy_to': 'agg_fields',
                'fields': {
                    'raw': {
                        'type': 'keyword'
                    }
                }
            }
        }
        resp = requests.put(
            _CONFIG['elasticsearch_url'] + '/' + index_name,
            data=json.dumps({
                'settings': {'index': {'number_of_shards': 3, 'number_of_replicas': 1}},
                'mappings': {'properties': test_mapping}
            }),
            headers={'Content-Type': 'application/json'}
        )
        if not resp.ok and resp.json()['error']['type'] != 'index_already_exists_exception':
            raise RuntimeError('Error creating index on ES:', resp.text)
    test_docs = [
        # Public doc
        {'obj_name': 'public-doc1',
         'is_public': True,
         'timestamp': 10,
         'creator': 'kbasesearchtest1',
         'shared_users': [],
         'creation_date': 'fakedate',
         'obj_id': 1,
         'version': 1,
         'copied': None,
         'tags': [],
         'access_group': 1,
         'obj_type_name': 'Typea'},
        {'obj_name': 'public-doc2', 'is_public': True, 'timestamp': 12,
         'creator': 'kbasesearchtest1',
         'shared_users': [],
         'creation_date': 'fakedate',
         'obj_id': 1,
         'version': 1,
         'copied': None,
         'tags': [],
         'access_group': 2, 'obj_type_name': 'Typeb'},
        # Private but accessible doc
        {'obj_name': 'private-doc1', 'is_public': False, 'timestamp': 7,
         'creator': 'kbasesearchtest1',
         'shared_users': [],
         'creation_date': 'fakedate',
         'obj_id': 1,
         'version': 1,
         'copied': None,
         'tags': [],
         'access_group': 1, 'obj_type_name': 'Typea'},
        # Private but inaccessible doc
        {'obj_name': 'private2-doc1', 'is_public': False, 'timestamp': 9,
         'creator': 'kbasesearchtest1',
         'shared_users': [],
         'creation_date': 'fakedate',
         'obj_id': 1,
         'version': 1,
         'copied': None,
         'tags': [],
         'access_group': 99, 'obj_type_name': 'Typeb'}
    ]
    for doc in test_docs:
        # Note that the 'refresh=wait_for' option must be set in the URL so we can search on it immediately.
        for i in range(0, 2):  # i will be [0, 1]
            url = '/'.join([  # type: ignore
                _CONFIG['elasticsearch_url'],
                _INDEX_NAMES[i],
                '_doc',
                doc['obj_name'],
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
        'timestamp': 15,
        'creator': 'kbasesearchtest1',
        'shared_users': [],
        'creation_date': 'fakedate',
        'obj_id': 1,
        'version': 1,
        'copied': None,
        'tags': []
    }
    url = '/'.join([
        _CONFIG['elasticsearch_url'],
        subobj_idx_name,
        '_doc',
        'featurexyz',
        '?refresh=wait_for'
    ])
    resp = requests.put(url, data=json.dumps(subobj_doc), headers={'Content-Type': 'application/json'})
    if not resp.ok:
        raise RuntimeError('Error creating doc on ES:', resp.text)

    # create default_search alias for all fields.
    url = '/'.join([
        _CONFIG['elasticsearch_url'],
        '_aliases'
    ])
    body = {
        "actions": [{"add": {"indices": _NON_SUB_NAMES, "alias": _CONFIG['index_prefix'] + ".default_search"}}]
    }
    resp = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
    if not resp.ok:
        raise RuntimeError("Error creating aliases on ES:", resp.text)
    print('elasticsearch aliases applied for legacy...')


def _tear_down_elasticsearch():
    """
    Drop the elasticsearch index when we exit the tests.
    """
    for index_name in _INDEX_NAMES:
        resp = requests.delete(_CONFIG['elasticsearch_url'] + '/' + index_name)
        if not resp.ok:
            print('Error tearing down ES index:', resp.text)
