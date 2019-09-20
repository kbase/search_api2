import requests
from .utils.config import init_config

_CONFIG = init_config()


def show_indexes(params, headers):
    """
    List all index names for our prefix
    """
    prefix = _CONFIG['index_prefix']
    resp = requests.get(
        _CONFIG['elasticsearch_url'] + '/_cat/indices/' + prefix + '*?format=json',
        headers={'Content-Type': 'application/json'},
    )
    if not resp.ok:
        raise RuntimeError(resp.text)
    resp_json = resp.json()
    return resp_json
