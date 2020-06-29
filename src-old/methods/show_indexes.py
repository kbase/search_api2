import re
import requests
from src.utils.config import init_config

_CONFIG = init_config()


def show_indexes(params, meta):
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
    result = []
    for each in resp_json:
        regex = f"^{_CONFIG['index_prefix']}."
        name = re.sub(regex, '', each['index'])
        idx = {
            'name': name,
            'count': int(each['docs.count'])
        }
        result.append(idx)
    return result
