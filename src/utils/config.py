import yaml
import urllib.request
import os
import functools


@functools.lru_cache(maxsize=2)
def init_config():
    """
    Initialize configuration data for the whole app
    """
    ws_url = os.environ.get('WORKSPACE_URL', 'https://ci.kbase.us/services/ws').strip('/')
    es_url = os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch:9200').strip('/')
    index_prefix = os.environ.get('INDEX_PREFIX', 'test')
    config_url = os.environ.get('GLOBAL_CONFIG_URL', 'https://github.com/kbase/index_runner_spec/releases/latest/download/config.yaml')  # noqa
    # Load the global configuration release (non-environment specific, public config)
    if not config_url.startswith('http'):
        raise RuntimeError(f"Invalid config url: {config_url}")
    with urllib.request.urlopen(config_url) as res:  # nosec
        global_config = yaml.safe_load(res)  # type: ignore
    return {
        'dev': bool(os.environ.get('DEVELOPMENT')),
        'global': global_config,
        'elasticsearch_url': es_url,
        'index_prefix': index_prefix,
        'workspace_url': ws_url
    }
