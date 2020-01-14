"""The main entrypoint for running the Flask server."""
import os
import sanic
import traceback
import requests
import time
import yaml
import jsonschema
from jsonschema.exceptions import ValidationError

from src.exceptions import InvalidParameters, UnknownMethod
from src.utils.config import init_config
from src.search_objects import search_objects
from src.handle_legacy import handle_legacy
from src.show_indexes import show_indexes
from src.check_if_doc_exists import check_if_doc_exists

app = sanic.Sanic()
_CONFIG = init_config()
_SCHEMAS_PATH = 'src/server/method_schemas.json'
with open(_SCHEMAS_PATH) as fd:
    _SCHEMAS = yaml.safe_load(fd)


@app.middleware('request')
async def cors_options(request):
    """Handle a CORS OPTIONS request."""
    if request.method == 'OPTIONS':
        return sanic.response.raw(b'', status=204)


@app.route('/')
@app.route('/status', methods=['GET', 'OPTIONS'])
async def health_check(request):
    """Really basic health check; could be expanded if needed."""
    return sanic.response.json({'status': 'ok'})


@app.route('/rpc', methods=['POST', 'OPTIONS'])
async def root(request):
    """Handle JSON RPC methods."""
    json_body = request.json  # TODO try/except
    req_id = json_body.get('id')
    method = json_body.get('method', 'show_config')
    params = json_body.get('params', {})
    if method not in _SCHEMAS:
        UnknownMethod(f'Unknown method: {method}. Available methods: {_RPC_HANDLERS.keys()}')
    param_schema = _SCHEMAS[method]['params']
    jsonschema.validate(params, param_schema)
    result = _RPC_HANDLERS[method](params, request.headers)  # type: ignore
    return sanic.response.json({
        'jsonrpc': "2.0",
        'result': result,
        'id': req_id
    })


@app.route('/legacy', methods=['POST', 'OPTIONS'])
async def legacy(request):
    """Handle legacy-formatted requests that are intended for the previous Java api."""
    result = handle_legacy(request.json, request.headers)
    return sanic.response.json(result)


def _show_config(params, headers):
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


# Function handlers for each rpc method.
_RPC_HANDLERS = {
    'show_config': _show_config,
    'search_objects': search_objects,
    'show_indexes': show_indexes,
    'check_if_doc_exists': check_if_doc_exists
}


@app.middleware('response')
async def cors_resp(req, res):
    """Handle cors response headers."""
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    res.headers['Access-Control-Allow-Headers'] = '*'


@app.exception(sanic.exceptions.NotFound)
async def page_not_found(request, err):
    return sanic.response.json("Path not found", status=404)


# TODO json parsing error

@app.exception(ValidationError)
async def params_invalid(request, err):
    resp = {
        'jsonrpc': '2.0',
        'id': request.json.get('id'),
        'error': {
            'code': -32602,
            'message': err.message,
            'data': {
                'failed_validator': err.validator,
                'value': err.instance,
                'path': list(err.absolute_path)
            }
        }
    }
    return sanic.response.json(resp, status=400)


@app.exception(UnknownMethod)
async def unknown_method(request, err):
    resp = {
        'jsonrpc': '2.0',
        'id': request.json.get('id'),
        'error': {
            'code': -32601,
            'message': str(err)
        }
    }
    return sanic.response.json(resp, status=400)


@app.exception(InvalidParameters)
async def invalid_params(request, err):
    resp = {
        'jsonrpc': '2.0',
        'id': request.json.get('id'),
        'error': {
            'code': -32602,
            'message': f'Invalid parameters: {err}'
        }
    }
    return sanic.response.json(resp, status=400)


# Any other exception -> 500
@app.exception(Exception)
async def server_error(request, err):
    print('=' * 80)
    print('500 Server Error')
    print('-' * 80)
    traceback.print_exc()
    print('=' * 80)
    resp = {
        'jsonrpc': '2.0',
        'id': request.json.get('id'),
        'error': {
            'code': -32000,
            'message': str(err),
            'data': {
                'class': err.__class__.__name__
            }
        }
    }
    return sanic.response.json(resp, status=500)


if __name__ == '__main__':
    print('Checking connection to elasticsearch..')
    elasticsearch_available = False
    while not elasticsearch_available:
        print('Attempting to connect to elasticsearch..')
        try:
            requests.get(_CONFIG['elasticsearch_url']).raise_for_status()
            print('Elasticsearch is online! Continuing..')
            elasticsearch_available = True
        except Exception:
            print('Unable to connect to Elasticsearch. Waiting..')
            time.sleep(5)
    app.run(
        host='0.0.0.0',  # nosec
        port=5000,
        workers=os.environ.get('WORKERS', 8),
        # debug=('DEVELOPMENT' in os.environ)  # XXX couldnt get autoreload to work
    )
