import requests
import json
from src.utils.config import config

# Define headers at module level
_BASE_HEADERS = {'Content-Type': 'application/json'}


def _get_headers():
    """Get headers with optional authorization."""
    headers = _BASE_HEADERS.copy()
    if config.get('authorization_header_value'):
        headers['Authorization'] = config['authorization_header_value']
    return headers


# Then use it in your functions:
def init_elasticsearch():
    """Initialize the indexes and documents on elasticsearch before running tests."""
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
    resp = requests.post(url, data=json.dumps(body), headers=_get_headers())
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
        headers=_get_headers(),
    )
    if not resp.ok and resp.json()['error']['type'] != 'index_already_exists_exception':
        raise RuntimeError('Error creating index on ES:', resp.text)


def create_doc(index_name, data):
    # Wait for doc to sync
    url = '/'.join([
        _ES_URL,
        index_name,
        '_doc',
        data['name'],
        '?refresh=wait_for'
    ])
    resp = requests.put(url, data=json.dumps(data), headers=_get_headers())
    if not resp.ok:
        raise RuntimeError(f"Error creating test doc:\n{resp.text}")