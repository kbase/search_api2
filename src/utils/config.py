import yaml
import urllib.request
import os


def init_config():
    ws_url = os.environ.get('WORKSPACE_URL', 'https://ci.kbase.us/services/ws').strip('/')
    es_url = os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch:9200').strip('/')
    index_prefix = os.environ.get('INDEX_PREFIX', 'test')
    config_url = os.environ.get('GLOBAL_CONFIG_URL', 'https://github.com/kbaseIncubator/search_config/releases/download/0.0.1/config.yaml')  # noqa
    # Load the global configuration release (non-environment specific, public config)
    with urllib.request.urlopen(config_url) as res:
        global_config = yaml.load(res)  # type: ignore
    return {
        'global': global_config,
        'elasticsearch_url': es_url,
        'index_prefix': index_prefix,
        'workspace_url': ws_url
    }
