"""The main entrypoint for running the Flask server."""
import json
import sanic
import traceback

from src.search1_rpc import service as legacy_service
from src.search2_rpc import service as rpc_service
from src.utils.config import config
from src.utils.logger import logger
from src.utils.wait_for_service import wait_for_service

app = sanic.Sanic(name='search2')


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
    result = rpc_service.call(body, {'auth': auth})
    return sanic.response.text(result, content_type='application/json')


@app.route('/legacy', methods=['POST', 'GET', 'OPTIONS'])
async def legacy(request):
    """Handle legacy-formatted requests that are intended for the previous Java api."""
    auth = request.headers.get('Authorization')
    body = _convert_rpc_formats(request.body)
    result = legacy_service.call(body, {'auth': auth})
    return sanic.response.text(result, content_type='application/json')


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
        data['id'] = '0'
    return json.dumps(data)


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
