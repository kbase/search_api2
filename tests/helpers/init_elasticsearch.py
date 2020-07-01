import requests
import json

from src.utils.config import config

index_names = [
    config['index_prefix'] + '.index1',
    config['index_prefix'] + '.index2',
]

_ES_URL = 'http://localhost:9200'

# Simple run once semaphore
_COMPLETED = False


def init_elasticsearch():
    """
    Initialize the indexes and documents on elasticsearch before running tests.
    """
    global _COMPLETED
    if _COMPLETED:
        return
    for index_name in index_names:
        # Check if exists
        resp = requests.head(_ES_URL + '/' + index_name)
        if resp.status_code == 200:
            continue
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
                _ES_URL,
                index_names[i],
                '_doc',
                doc['name'],
                '?refresh=wait_for'
            ])
            resp = requests.put(url, data=json.dumps(doc), headers={'Content-Type': 'application/json'})
            if not resp.ok:
                raise RuntimeError('Error creating doc on ES:', resp.text)

    # create default_search alias for all fields.
    url = '/'.join([
        _ES_URL,
        '_aliases'
    ])
    body = {
        "actions": [{"add": {"indices": index_names, "alias": config['index_prefix'] + ".default_search"}}]
    }
    resp = requests.post(url, data=json.dumps(body), headers={'Content-Type': 'application/json'})
    if not resp.ok:
        raise RuntimeError("Error creating aliases on ES:", resp.text)
    _COMPLETED = True
