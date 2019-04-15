import os


def init_config():
    ws_url = os.environ.get('WORKSPACE_URL', 'https://ci.kbase.us/services/ws').strip('/')
    es_url = os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch:9200').strip('/')
    index_prefix = os.environ.get('INDEX_PREFIX', 'test')
    return {
        'elasticsearch_url': es_url,
        'index_prefix': index_prefix,
        'workspace_url': ws_url
    }
