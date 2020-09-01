import yaml
import urllib.request
import os


def init_config():
    """
    Initialize configuration data for the whole app
    """
    ws_url = os.environ.get('WORKSPACE_URL', 'https://ci.kbase.us/services/ws').strip('/')
    es_url = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200').strip('/')
    index_prefix = os.environ.get('INDEX_PREFIX', 'test')
    prefix_delimiter = os.environ.get('INDEX_PREFIX_DELIMITER', '_')
    config_url = os.environ.get(
        'GLOBAL_CONFIG_URL',
        'https://github.com/kbase/index_runner_spec/releases/latest/download/config.yaml'
    )
    user_profile_url = os.environ.get(
        'USER_PROFILE_URL',
        'https://ci.kbase.us/services/user_profile/rpc/'
    )
    # Load the global configuration release (non-environment specific, public config)
    allowed_protocols = ('https://', 'http://', 'file://')
    matches_protocol = (config_url.startswith(prot) for prot in allowed_protocols)
    if not any(matches_protocol):
        raise RuntimeError(f"Invalid config url: {config_url}")
    with urllib.request.urlopen(config_url) as res:  # nosec
        global_config = yaml.safe_load(res)
    with open('VERSION') as fd:
        app_version = fd.read().replace('\n', '')
    return {
        'dev': bool(os.environ.get('DEVELOPMENT')),
        'global': global_config,
        'elasticsearch_url': es_url,
        'index_prefix': index_prefix,
        'prefix_delimiter': prefix_delimiter,
        'workspace_url': ws_url,
        'user_profile_url': user_profile_url,
        'workers': int(os.environ.get('WORKERS', 8)),
        'app_version': app_version,
    }


config = init_config()
