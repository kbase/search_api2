import request
import jsonschema
from sanic.exceptions import NotFound

schema = {
    'type': 'object'
    'properties': {
        'doc_id': {'type': 'string'},
        'index': {'type': 'string'},
        'es_datatype': {'type': 'string'}
    } 
}


def check_if_doc_exists(params, headers, config):
    """
    Given
    params:
        doc_id - in format "DataSource:workspace_id:object_id"
        index - elasticsearch index to search (required)
        es_datatype - elasticsearch document data type
    """
    # verify inputs
    jsonschema.validate(instance=params, schema=schema)
    index = config['index_prefix'] + '.' + params['index']

    resp = requests.head(
        config['elasticsearch_url'] + '/' + index + '/' + params.get('es_datatype', 'data') + '/' + params['doc_id']
    )
    if resp.status_code == 200:
        return {
            'result': True
        }
    else:
        # error we are not interested in...
        raise RuntimeError(resp.text)

@app.exception(NotFound)
async def I_AM_NOT_FOUND_WOWWIIEEE(request, exception):
    return exception
