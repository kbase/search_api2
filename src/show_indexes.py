import requests


def show_indexes(params, headers, config):
    """
    List all index names for our prefix
    """
    prefix = config['index_prefix']
    resp = requests.get(
        config['elasticsearch_url'] + '/_cat/indices/' + prefix + '*?format=json',
        headers={'Content-Type': 'application/json'}
    )
    if not resp.ok:
        raise RuntimeError(resp.text)
    resp_json = resp.json()
    return resp_json
