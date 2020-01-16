import requests
import sanic
import logging
from src.utils.config import init_config

_CONFIG = init_config()

logger = logging.getLogger('searchapi2')


def check_if_doc_accessible(params, headers):
    """
    Check whether a particular document exists somewhere in elasticsearch.
    See method_schemas.json for a definition of the params
    """
    index = _CONFIG['index_prefix'] + '.' + params['index']
    url = _CONFIG['elasticsearch_url'] + '/' + index + '/_doc/' + params['doc_id']
    resp = requests.head(url)
    if resp.ok:
        return resp
    elif resp.status_code == 404:
        raise sanic.exceptions.NotFound(f"Document with ID '{params['doc_id']}' does not exist.")
    else:
        # Some other unexpected status (eg. elastic is down)
        logger.error(f'Got response code {resp.status_code} from Elasticsearch:\n{resp.text}')
        raise RuntimeError(resp.text)
