"""The main entrypoint for running the Flask server."""
import json
import sanic
import time
import traceback

from src.search1_rpc import service as legacy_service
from src.search2_rpc import service as rpc_service
from src.utils.config import config
from src.utils.logger import logger
from src.utils.obj_utils import get_path
from src.utils.wait_for_service import wait_for_service

app = sanic.Sanic(name='search2')

# Mapping of JSON-RPC status code to HTTP response status
_ERR_STATUS = {
    -32000: 500,  # Server error
    -34001: 401,  # Unauthorized
    -32005: 404,  # Type not found
    -32002: 404,  # Index not found
}


# TODO: services should not implement CORS - it should be handled
# by the services proxy
@app.middleware('request')
async def cors_options(request):
    """Handle a CORS OPTIONS request."""
    if request.method == 'OPTIONS':
        return sanic.response.raw(b'', status=204)


@app.route('/', methods=['GET', 'OPTIONS'])
@app.route('/status', methods=['GET', 'OPTIONS'])
async def health_check(request):
    """No-op."""
    return sanic.response.raw(b'')


@app.route('/rpc', methods=['POST', 'GET', 'OPTIONS'])
async def root(request):
    """Handle JSON RPC methods."""
    auth = request.headers.get('Authorization')
    body = _convert_rpc_formats(request.body)
    result = rpc_service.call_py(body, {'auth': auth})
    status = _get_status_code(result)
    return sanic.response.json(result, status=status)


@app.route('/legacy', methods=None)
async def legacy(request):
    """Handle legacy-formatted requests that are intended for the previous Java api."""
    # Manually handle these, so as not to inflame sanic into handling
    # unhandled method errors.
    if request.method != 'POST':
        return sanic.response.raw(b'', status=405)
    auth = request.headers.get('Authorization')
    result = legacy_service.call(request.body, {'auth': auth})
    return sanic.response.raw(
        bytes(result, 'utf-8'),
        headers={'content-type': 'application/json'})


@app.middleware('response')
async def cors_resp(req, res):
    """Handle cors response headers."""
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    res.headers['Access-Control-Allow-Headers'] = '*'


@app.exception(sanic.exceptions.NotFound)
async def page_not_found(request, err):
    return sanic.response.raw(b'', status=404)


@app.exception(Exception)
async def any_exception(request, err):
    """
    Handle any unexpected server error.
    Theoretically, this should never be reached. JSONRPCBase will handle method
    error responses.
    TODO: This assumes JSON-RPC 2.0 for all calls handled by this server;
    yet the legacy api is JSON-RPC 1.1.
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


def _convert_rpc_formats(body: str):
    """
    For compatibility reasons, we want to be very liberal in the RPC request
    format we allow. For JSON-RPC version 1.1 requests, we convert the format
    to JSON-RPC 2.0 for our JSONRPCService. If both of "version", "jsonrpc" are
    left out, then we fill it in for them. We also fill in the "id" field, so
    that notification style requests are always avoided.
    Of course, these conversion are violations of the JSON-RPC 2.0 spec. But we
    are prioritizing backwards compatibility here.
    """
    try:
        data = json.loads(body)
    except Exception:
        # Let the JSONRPCService handle the error
        return body
    if 'version' in data:
        del data['version']
    if 'version' not in data and 'jsonrpc' not in data:
        data['jsonrpc'] = '2.0'
    if 'id' not in data:
        data['id'] = int(time.time() * 1000)
    return data


def _get_status_code(result: dict) -> int:
    """
    Create an HTTP status code from a JSON-RPC response
    Technically, JSON-RPC could ignore HTTP status codes. But for the sake of
    usability and convenience, we return non-2xx status codes when there is an
    error.
    """
    error_code = get_path(result, ['error', 'code'])
    if error_code is not None:
        return _ERR_STATUS.get(error_code, 400)
    return 200


# Wait for dependencies to start
logger.info('Checking connection to elasticsearch')
wait_for_service(config['elasticsearch_url'], 'Elasticsearch')
# Start the server
app.run(
    host='0.0.0.0',  # nosec
    port=5000,
    workers=config['workers'],
    debug=config['dev'],
)
