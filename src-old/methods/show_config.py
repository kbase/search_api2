from src.utils.config import init_config

_CONFIG = init_config()


def show_config(params, meta):
    """
    Display publicly readable configuration settings for this server.
    Be sure to add new entries here explicitly so that nothing is shown unintentionally.
    """
    return {
        'elasticsearch_url': _CONFIG['elasticsearch_url'],
        'workspace_url': _CONFIG['workspace_url'],
        'index_prefix': _CONFIG['index_prefix'],
        'global': _CONFIG['global']
    }
