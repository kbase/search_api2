from unittest.mock import patch
import subprocess

from src.search1_conversion import convert_result
from src.utils.wait_for_service import wait_for_service
from tests.helpers import init_elasticsearch

from tests.search1_conversion.test_data import (
    mock_ws_info,
    mock_user_profiles,
    test_search_results,
)

ES_URL = 'http://localhost:9200'
subprocess.run("docker-compose up -d", shell=True)
wait_for_service(ES_URL, 'Elasticsearch')
init_elasticsearch()


def test_search_objects_valid():
    params = {
        'post_processing': {
        }
    }
    expected = {
      "pagination": {},
      "sorting_rules": [],
      "total": 0,
      "search_time": 1,
      "objects": [
        {
          "object_name": "",
          "access_group": 1,
          "obj_id": None,
          "version": None,
          "timestamp": 0,
          "type": "",
          "creator": None,
          "data": {
            "name": "name1",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "key_props": {
            "name": "name1",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "guid": "WS:1/1",
          "kbase_id": "1/1",
          "index_name": "test",
          "type_ver": 0,
          "highlight": {},
          "name": "<em>name1</em>"
        },
        {
          "object_name": "",
          "access_group": 0,
          "obj_id": None,
          "version": None,
          "timestamp": 0,
          "type": "",
          "creator": None,
          "data": {
            "name": "name2",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "key_props": {
            "name": "name2",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "guid": "WS:1/1",
          "kbase_id": "1/1",
          "index_name": "test",
          "type_ver": 0,
          "highlight": {},
          "name": "<em>name2</em>"
        }
      ],
      "access_group_narrative_info": {'1': ['', 0, 1591415395, 'username', 'User Example']},
      "access_groups_info": {'0': mock_ws_info, '1': mock_ws_info}
    }
    with patch('src.search1_conversion.convert_result.get_workspace_info') as ws_patched:
        with patch('src.search1_conversion.convert_result.get_user_profiles') as user_patched:
            ws_patched.return_value = mock_ws_info
            user_patched.return_value = mock_user_profiles
            final = convert_result.search_objects(params, test_search_results, {'auth': None})
    for key in expected:
        assert key in final
        assert expected[key] == final[key], key


def test_get_objects_valid():
    params = {
        'post_processing': {
        }
    }
    expected = {
      "search_time": 1,
      "objects": [
        {
          "object_name": "",
          "access_group": 1,
          "obj_id": None,
          "version": None,
          "timestamp": 0,
          "type": "",
          "creator": None,
          "data": {
            "name": "name1",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "key_props": {
            "name": "name1",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "guid": "WS:1/1",
          "kbase_id": "1/1",
          "index_name": "test",
          "type_ver": 0,
          "highlight": {},
          "name": "<em>name1</em>"
        },
        {
          "object_name": "",
          "access_group": 0,
          "obj_id": None,
          "version": None,
          "timestamp": 0,
          "type": "",
          "creator": None,
          "data": {
            "name": "name2",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "key_props": {
            "name": "name2",
            "creator": "",
            "shared_users": [],
            "timestamp": 0,
            "creation_date": "",
            "is_public": False,
            "access_group": 0,
            "obj_id": 0,
            "version": 0,
            "copied": None,
            "tags": []
          },
          "guid": "WS:1/1",
          "kbase_id": "1/1",
          "index_name": "test",
          "type_ver": 0,
          "highlight": {},
          "name": "<em>name2</em>"
        }
      ],
      "access_group_narrative_info": {'1': ['', 0, 1591415395, 'username', 'User Example']},
      "access_groups_info": {'0': mock_ws_info, '1': mock_ws_info}
    }
    with patch('src.search1_conversion.convert_result.get_workspace_info') as ws_patched:
        with patch('src.search1_conversion.convert_result.get_user_profiles') as user_patched:
            ws_patched.return_value = mock_ws_info
            user_patched.return_value = mock_user_profiles
            final = convert_result.get_objects(params, test_search_results, {'auth': None})
    print('FINAL', final)
    for key in expected:
        assert key in final
        assert expected[key] == final[key], key


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
