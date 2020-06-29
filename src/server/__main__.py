"""The main entrypoint for running the Flask server."""
import sanic
import traceback

from src.utils.config import config
from src.utils.logger import logger
from src.utils.wait_for_service import wait_for_service

app = sanic.Sanic(name='search2')


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
    return sanic.response.text('{}', content_type='application/json')
    # auth = request.headers.get('Authorization')
    # result = service.call(request.body, {'auth': auth})
    # return sanic.response.text(result, content_type='application/json')


@app.route('/legacy', methods=['POST', 'GET', 'OPTIONS'])
async def legacy(request):
    """Handle legacy-formatted requests that are intended for the previous Java api."""
    return sanic.response.text('{}', content_type='application/json')
    # auth = request.headers.get('Authorization')
    # result = legacy_service.call(request.body, {'auth': auth})
    # return sanic.response.text(result, content_type='application/json')


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
