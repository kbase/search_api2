"""The main entrypoint for running the Flask server."""
import flask
import json
import os
from uuid import uuid4
import traceback
from jsonschema.exceptions import ValidationError

from src.exceptions import MissingHeader, UnauthorizedAccess, InvalidParameters
from src.utils.config import init_config
from src.search_objects import search_objects

# All api version modules, from oldest to newest
app = flask.Flask(__name__)
app.config['DEBUG'] = os.environ.get('DEVELOPMENT', True)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', str(uuid4()))
app.url_map.strict_slashes = False  # allow both `get /v1/` and `get /v1`


@app.route('/', methods=['POST'])
def root():
    """Handle JSON RPC methods."""
    try:
        json_body = json.loads(flask.request.get_data())
    except Exception:
        raise InvalidParameters('Pass in a JSON body with RPC parameters.')
    method = json_body.get('method', 'show_config')
    params = json_body.get('params')
    rpc_handlers = {
        'show_config': _show_config,
        'search_objects': search_objects
    }
    if method not in rpc_handlers:
        InvalidParameters(f'Unknown method: {method}. Available methods: {rpc_handlers.keys()}')
    config = init_config()
    result = rpc_handlers[method](params, config)
    return flask.jsonify(result)


def _show_config(params, config):
    """
    Display publicly readable configuration settings for this server.
    Be sure to add new entries here explicitly so that nothing is shown unintentionally.
    """
    return {
        'elasticsearch_url': config['elasticsearch_url'],
        'workspace_url': config['workspace_url'],
        'index_prefix': config['index_prefix']
    }


@app.errorhandler(InvalidParameters)
def invalid_params(err):
    """Invalid request body json params."""
    resp = {'error': str(err)}
    return (flask.jsonify(resp), 400)


@app.errorhandler(ValidationError)
def validation_error(err):
    """Json Schema validation error."""
    resp = {
        'error': str(err).split('\n')[0],
        'instance': err.instance,
        'validator': err.validator,
        'validator_value': err.validator_value,
        'schema': err.schema
    }
    return (flask.jsonify(resp), 400)


@app.errorhandler(UnauthorizedAccess)
def unauthorized_access(err):
    resp = {
        'error': '403 - Unauthorized',
        'auth_url': err.auth_url,
        'auth_response': err.response
    }
    return (flask.jsonify(resp), 403)


@app.errorhandler(404)
def page_not_found(err):
    return (flask.jsonify({'error': '404 - Not found.'}), 404)


@app.errorhandler(405)
def method_not_allowed(err):
    return (flask.jsonify({'error': '405 - Method not allowed.'}), 405)


@app.errorhandler(MissingHeader)
def generic_400(err):
    return (flask.jsonify({'error': str(err)}), 400)


# Any other unhandled exceptions -> 500
@app.errorhandler(Exception)
@app.errorhandler(500)
def server_error(err):
    print('=' * 80)
    print('500 Unexpected Server Error')
    print('-' * 80)
    traceback.print_exc()
    print('=' * 80)
    resp = {'error': '500 - Unexpected server error'}
    resp['error_class'] = err.__class__.__name__
    resp['error_details'] = str(err)
    return (flask.jsonify(resp), 500)


@app.after_request
def after_request(resp):
    # Log request
    print(' '.join([flask.request.method, flask.request.path, '->', resp.status]))
    # Enable CORS
    resp.headers['Access-Control-Allow-Origin'] = '*'
    env_allowed_headers = os.environ.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS', 'Authorization, Content-Type')
    resp.headers['Access-Control-Allow-Headers'] = env_allowed_headers
    # Set JSON content type and response length
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Content-Length'] = resp.calculate_content_length()
    return resp
