import requests

def check_if_doc_exists(params, headers, config):
    """
    Given
    params:
        doc_id - in format "DataSource:workspace_id:object_id"
        index - elasticsearch index to search (required)
        es_datatype - elasticsearch document data type
    """
    # verify inputs
    if not params.get("doc_id"):
        # bad
        pass
    if not params.get('index'):
        # bad
        pass
    if not params.get('es_datatype'):
        # bad
        pass

    doc_id = params['doc_id']
    index = config['index_prefix'] + '.' + params['index']
    es_datatype = params.get('es_datatype', 'data')

    resp = requests.head(
        config['elasticsearch_url'] + '/' + index + '/' + es_datatype + '/' + doc_id
    )
    if resp.status_code == 200:
        return {
            'result': True
        }
    elif resp.status_code == 404:
        # does not exist.
        return {
            'result': False
        }
    else:
        # error
        return {
            'error': f'returned with status code: {resp.status_code}'
        }
