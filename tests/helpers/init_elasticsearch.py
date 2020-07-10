import requests
import json

from src.utils.config import config

# TODO use a util for creating index names
narrative_index_name = ''.join([
    config['index_prefix'],
    config['prefix_delimiter'],
    config['global']['ws_type_to_indexes']['KBaseNarrative.Narrative'],
])

index_names = [
    config['index_prefix'] + config['prefix_delimiter'] + 'index1',
    config['index_prefix'] + config['prefix_delimiter'] + 'index2',
]

_ES_URL = 'http://localhost:9200'

# Simple run once semaphore
_COMPLETED = False

test_docs = [
    # Public doc
    {'name': 'public-doc1', 'access_group': '1', 'is_public': True, 'timestamp': 10},
    # Public doc
    {'name': 'public-doc2', 'access_group': '99', 'is_public': True, 'timestamp': 12},
    # Private but accessible doc
    {'name': 'private-doc1', 'is_public': False, 'access_group': '1', 'timestamp': 7},
    # Private but inaccessible doc
    {'name': 'private2-doc1', 'is_public': False, 'access_group': '99', 'timestamp': 9},
]

narrative_docs = [
        {
            'name': 'narrative1',
            'narrative_title': 'narrative1',
            'is_public': True,
            'obj_id': 123,
            'access_group': '1',
            'timestamp': 1,
        },
]


def init_elasticsearch():
    """
    Initialize the indexes and documents on elasticsearch before running tests.
    """
    global _COMPLETED
    if _COMPLETED:
        return
    for index_name in index_names:
        create_index(index_name)
    create_index(narrative_index_name)
    for index_name in index_names:
        for doc in test_docs:
            create_doc(index_name, doc)
    for doc in narrative_docs:
        create_doc(narrative_index_name, doc)
    # create default_search alias for all fields.
    url = f"{_ES_URL}/_aliases"
    alias_name = config['index_prefix'] + config['prefix_delimiter'] + "default_search"
    body = {
        "actions": [
            {"add": {"indices": index_names, "alias": alias_name}}
        ]
    }
    resp = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
    if not resp.ok:
        raise RuntimeError("Error creating aliases on ES:", resp.text)
    _COMPLETED = True


def create_index(index_name):
    # Check if exists
    resp = requests.head(_ES_URL + '/' + index_name)
    if resp.status_code == 200:
        return
    resp = requests.put(
        _ES_URL + '/' + index_name,
        data=json.dumps({
            'settings': {
                'index': {'number_of_shards': 2, 'number_of_replicas': 1}
            }
        }),
        headers={'Content-Type': 'application/json'},
    )
    if not resp.ok and resp.json()['error']['type'] != 'index_already_exists_exception':
        raise RuntimeError('Error creating index on ES:', resp.text)


def create_doc(index_name, data):
    # Wait for doc to sync
    url = '/'.join([  # type: ignore
        _ES_URL,
        index_name,
        '_doc',
        data['name'],
        '?refresh=wait_for'
    ])
    headers = {'Content-Type': 'application/json'}
    resp = requests.put(url, data=json.dumps(data), headers=headers)
    if not resp.ok:
        raise RuntimeError(f"Error creating test doc:\n{resp.text}")
