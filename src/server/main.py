"""The main entrypoint for running the Flask server."""
import os
import sanic
import requests
import time
import yaml
import logging
import sys
import traceback
from jsonrpcbase import JSONRPCService

from src.utils.config import init_config
from src.methods.search_objects import search_objects
from src.methods.show_indexes import show_indexes
from src.methods.show_config import show_config
import src.legacy_methods.main as legacy_methods

# Initialize the server, config, logger, and RPC APIs
_CONFIG = init_config()

logger = logging.getLogger('searchapi2')

_SCHEMAS_PATH = 'src/server/method_schemas.yaml'
with open(_SCHEMAS_PATH) as fd:
    _SCHEMAS = yaml.safe_load(fd)

service = JSONRPCService()
service.add(show_config, schema=_SCHEMAS['show_config'])
service.add(search_objects, schema=_SCHEMAS['search_objects'])
service.add(show_indexes, schema=_SCHEMAS['show_indexes'])

legacy_service = JSONRPCService()
legacy_service.add(legacy_methods.server_status, name='KBaseSearchEngine.status')
legacy_service.add(legacy_methods.search_objects, name='KBaseSearchEngine.search_objects')
legacy_service.add(legacy_methods.search_types, name='KBaseSearchEngine.search_types')
legacy_service.add(legacy_methods.list_types, name='KBaseSearchEngine.list_types')
legacy_service.add(legacy_methods.get_objects, name='KBaseSearchEngine.get_objects')
# legacy_service.add(methods.search_objects2, 'KBaseSearchEngine.search_objects2')
# legacy_service.add(methods.search_types2, 'KBaseSearchEngine.search_types2')
# legacy_service.add(methods.get_objects2, 'KBaseSearchEngine.get_objects2')

app = sanic.Sanic(name='searchapi2')


@app.middleware('request')
async def cors_options(request):
    """Handle a CORS OPTIONS request."""
    if request.method == 'OPTIONS':
        return sanic.response.raw(b'', status=204)


@app.route('/')
@app.route('/status', methods=['GET', 'OPTIONS'])
async def health_check(request):
    """No-op."""
    return sanic.response.raw(b'')


@app.route('/rpc', methods=['POST', 'GET', 'OPTIONS'])
async def root(request):
    """Handle JSON RPC methods."""
    auth = request.headers.get('Authorization')
    result = service.call(request.body, {'auth': auth})
    return sanic.response.text(result, content_type='application/json')


@app.route('/legacy', methods=['POST', 'OPTIONS'])
async def legacy(request):
    """Handle legacy-formatted requests that are intended for the previous Java api."""
    auth = request.headers.get('Authorization')
    result = legacy_service.call(request.body, {'auth': auth})
    return sanic.response.text(result, content_type='application/json')


@app.middleware('response')
async def cors_resp(req, res):
    """Handle cors response headers."""
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    res.headers['Access-Control-Allow-Headers'] = '*'


@app.exception(sanic.exceptions.NotFound)
async def page_not_found(request, err):
    return sanic.response.json("Path not found", status=404)


@app.exception(Exception)
async def any_exception(request, err):
    """
    Handle any unexpected server error.
    Ideally, this should never be reached. JSONRPCBase will handle method error responses.
    """
    traceback.print_exc()
    return sanic.response.json({
        "jsonrpc": "2.0",
        "error": {
            "code": -32000,
            "message": "Server error",
            "data": {
                "error": str(err),
            }
        }
    }, status=500)


def init_logger():
    """
    Initialize log settings. Mutates the `logger` object.
    """
    # Set the log level
    level = os.environ.get('LOGLEVEL', 'DEBUG').upper()
    logger.setLevel(level)
    logger.propagate = False  # Don't print duplicate messages
    logging.basicConfig(level=level)
    # Create the formatter
    fmt = "%(asctime)s %(levelname)-8s %(message)s (%(filename)s:%(lineno)s)"
    time_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, time_fmt)
    # Stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    print(f'Logger and level: {logger}')


if __name__ == '__main__':
    # Quiet the urllib3 logger
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    init_logger()
    # Wait for dependencies to start
    logger.info('Checking connection to elasticsearch..')
    elasticsearch_available = False
    while not elasticsearch_available:
        logger.info('Attempting to connect to elasticsearch..')
        try:
            requests.get(_CONFIG['elasticsearch_url']).raise_for_status()
            logger.info('Elasticsearch is online! Continuing..')
            elasticsearch_available = True
        except Exception:
            logger.info('Unable to connect to Elasticsearch. Waiting..')
            time.sleep(5)
    # Start the server
    app.run(
        host='0.0.0.0',  # nosec
        port=5000,
        workers=os.environ.get('WORKERS', 8),
        debug=('DEVELOPMENT' in os.environ)
    )
