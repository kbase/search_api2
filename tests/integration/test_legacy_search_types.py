from tests.helpers.integration_setup import do_rpc, load_data_file


def test_search_types(service):
    request_data = load_data_file('search_types', 'case-05-request.json')
    response_data = load_data_file('search_types', 'case-05-response.json')
    url = service['app_url'] + '/legacy'
    res = do_rpc(url, request_data, response_data)
    assert res['search_time'] > 0
    assert res['type_to_count']  # TODO match more closely when things are more indexed

