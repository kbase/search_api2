import yaml
import urllib.request
import os
import base64
import logging

logger = logging.getLogger('search2')


def init_config():
    """
    Initialize configuration data for the whole app
    """
    # TODO: it might be better to NOT default to testing configuration,
    #       but rather explicitly set the test environment.
    #       Reason? A failure to configure one of these in prod could lead to
    #       confusing failure conditions.
    ws_url = os.environ.get('WORKSPACE_URL', 'https://ci.kbase.us/services/ws').strip('/')
    es_url = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200').strip('/')
    es_auth_username = os.environ.get('ELASTICSEARCH_AUTH_USERNAME')
    es_auth_password = os.environ.get('ELASTICSEARCH_AUTH_PASSWORD')
    index_prefix = os.environ.get('INDEX_PREFIX', 'test')
    prefix_delimiter = os.environ.get('INDEX_PREFIX_DELIMITER', '.')
    suffix_delimiter = os.environ.get('INDEX_SUFFIX_DELIMITER', '_')
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
        'elasticsearch_auth_username': es_auth_username,
        'elasticsearch_auth_password': es_auth_password,
        'index_prefix': index_prefix,
        'prefix_delimiter': prefix_delimiter,
        'suffix_delimiter': suffix_delimiter,
        'workspace_url': ws_url,
        'user_profile_url': user_profile_url,
        'workers': int(os.environ.get('WORKERS', 8)),
        'app_version': app_version,
    }


config = init_config()


def get_elasticsearch_auth_header():
    """
    Build the Elasticsearch Authorization header based on available credentials.
    Returns None if no credentials are configured.

    Uses Basic authentication with username and password.
    """
    username = config.get('elasticsearch_auth_username')
    password = config.get('elasticsearch_auth_password')

    if username and password:
        # Basic authentication with base64 encoding
        credentials = f"{username}:{password}"
        credentials_bytes = credentials.encode('utf-8')
        base64_credentials = base64.b64encode(credentials_bytes).decode('utf-8')
        logger.info("Using Basic Authentication for Elasticsearch.")
        return f"Basic {base64_credentials}"
    else:
        return None
