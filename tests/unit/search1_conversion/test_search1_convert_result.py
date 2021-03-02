from unittest import mock
import json
from src.search1_conversion import convert_result

from tests.unit.search1_conversion.data import (
    mock_ws_info,
    mock_user_profiles,
    test_search_results,
    expected_search_results,
    expected_get_objects,
)

original_expected = json.dumps(expected_search_results)


# TODO test post processing
# TODO test the following fields: object_name, obj_id, version, type, creator


def mocked_get_workspace_info(workspace_id, auth_token):
    # if auth provided, assume the private workspaces.
    info = mock_ws_info.get(str(workspace_id))
    if info is not None:
        if auth_token is not None:
            # private and public workspaces, if either
            # public or user perms are not n (no access)
            # can access.
            if info[6] != 'n' or info[5] != 'n':
                return info
        else:
            # public workspaces
            if info[6] != 'n':
                return info

    return None


@mock.patch('src.search1_conversion.convert_result.get_workspace_info')
@mock.patch('src.search1_conversion.convert_result.get_user_profiles')
def test_search_objects_valid(get_user_profiles_patched, get_workspace_info_patched, services):
    get_workspace_info_patched.side_effect = mocked_get_workspace_info
    get_user_profiles_patched.return_value = mock_user_profiles

    params = {
        'post_processing': {
            'add_narrative_info': 1,
            'add_access_group_info': 1,
            'include_highlight': 1,
        }
    }

    final = convert_result.search_objects(params, test_search_results, {'auth': None})

    for key in expected_search_results:
        assert key in final
        assert expected_search_results[key] == final[key], key


@mock.patch('src.search1_conversion.convert_result.get_workspace_info')
@mock.patch('src.search1_conversion.convert_result.get_user_profiles')
def test_get_objects_valid(get_user_profiles_patched, get_workspace_info_patched, services):
    get_workspace_info_patched.side_effect = mocked_get_workspace_info
    get_user_profiles_patched.return_value = mock_user_profiles

    params = {
        'post_processing': {
            'add_narrative_info': 1,
            'add_access_group_info': 1,
            'include_highlight': 1,
        }
    }

    final = convert_result.get_objects(params, test_search_results, {'auth': None})
    for key in expected_get_objects:
        assert key in final
        assert expected_get_objects[key] == final[key], key


def test_search_types_valid(services):
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
    for key in expected:
        assert key in final
        assert expected[key] == final[key], key
