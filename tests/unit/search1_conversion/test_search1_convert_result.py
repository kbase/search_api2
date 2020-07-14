from unittest.mock import patch
import subprocess

from src.search1_conversion import convert_result
from src.utils.wait_for_service import wait_for_service
from tests.helpers import init_elasticsearch

from tests.unit.search1_conversion.data import (
    mock_ws_info,
    mock_user_profiles,
    test_search_results,
    expected_search_results,
    expected_get_objects,
)

ES_URL = 'http://localhost:9200'
subprocess.run("docker-compose up -d", shell=True)
wait_for_service(ES_URL, 'Elasticsearch')
init_elasticsearch()

# TODO test post processing
# TODO test the following fields: object_name, obj_id, version, type, creator


def test_search_objects_valid():
    params = {
        'post_processing': {
            'add_narrative_info': 1,
            'add_access_group_info': 1,
        }
    }
    with patch('src.search1_conversion.convert_result.get_workspace_info') as ws_patched:
        with patch('src.search1_conversion.convert_result.get_user_profiles') as user_patched:
            ws_patched.return_value = mock_ws_info
            user_patched.return_value = mock_user_profiles
            final = convert_result.search_objects(params, test_search_results, {'auth': None})
    for key in expected_search_results:
        assert key in final
        assert expected_search_results[key] == final[key], key


def test_get_objects_valid():
    params = {
        'post_processing': {
            'add_narrative_info': 1,
            'add_access_group_info': 1,
        }
    }
    with patch('src.search1_conversion.convert_result.get_workspace_info') as ws_patched:
        with patch('src.search1_conversion.convert_result.get_user_profiles') as user_patched:
            ws_patched.return_value = mock_ws_info
            user_patched.return_value = mock_user_profiles
            final = convert_result.get_objects(params, test_search_results, {'auth': None})
    for key in expected_get_objects:
        assert key in final
        assert expected_get_objects[key] == final[key], key


def test_search_types_valid():
    params = {
        'post_processing': {
        }
    }
    test_results = {
        'search_time': 1,
        'hits': [],
        'aggregations': {
            'type_count': {
                'counts': [
                    {'key': 'x', 'count': 10},
                    {'key': 'y', 'count': 20},
                ]
            }
        }
    }
    expected = {
      "search_time": 1,
      "type_to_count": {
          'x': 10,
          'y': 20,
      },
    }
    final = convert_result.search_types(params, test_results, {'auth': None})
    print('FINAL', final)
    for key in expected:
        assert key in final
        assert expected[key] == final[key], key
