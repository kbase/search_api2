import json
import os


def get_data(name):
    """Load the json test data file with the given name from ./data/legacy """

    file_path = os.path.join(os.path.dirname(__file__), 'data', name)
    if os.path.isfile(file_path):
        with open(file_path) as f:
            return True, json.load(f)
    else:
        return False, None


def mocked_get_workspace_info(workspace_id, auth_token):
    # if auth provided, assume the private workspaces.
    found, info = get_data(f'Workspace/get_workspace_info/{workspace_id}.json')
    if not found:
        return None

    # Variable names taken from workspace spec
    [_id, _workspace, _owner, _moddate, _max_objid, user_permission, globalread,
     _lockstat, _metadata] = info
    if auth_token is not None:
        # If authenticated, access is granted if either
        # public (globalread) or private (user_permission) is
        # not denied ('n')
        if globalread != 'n' or user_permission != 'n':
            return info
    else:
        # Without authentication, access is granted only if
        # public (globalread) is not denied
        if globalread != 'n':
            return info

    return None


def mocked_get_user_profiles(usernames, token=None):
    """
    mocks get_user_profiles in src/utils/user_profiles.py

    :param usernames:
    :return:
    """
    profiles = []
    for username in usernames:
        found, profile = get_data(f'UserProfile/get_profile/{username}.json')
        if not found:
            profiles.append(None)
        else:
            profiles.append(profile)
    return profiles


def handle_get_workspace_info(rpc, auth_token):
    workspace_id = rpc['params'][0]['id']
    # if auth provided, assume the private workspaces.
    found, info = get_data(f'Workspace/get_workspace_info/{workspace_id}.json')
    if not found:
        return None

    # Variable names taken from workspace spec
    [_id, _workspace, _owner, _moddate, _max_objid, user_permission, globalread,
     _lockstat, _metadata] = info
    if auth_token is not None:
        # If authenticated, access is granted if either
        # public (globalread) or private (user_permission) is
        # not denied ('n')
        if globalread != 'n' or user_permission != 'n':
            return info
    else:
        # Without authentication, access is granted only if
        # public (globalread) is not denied
        if globalread != 'n':
            return info

    return None


def handle_get_user_profile(rpc, auth_token):
    usernames = rpc['params'][0]
    profiles = []
    for username in usernames:
        found, profile = get_data(f'UserProfile/get_profile/{username}.json')
        if not found:
            profiles.append(None)
        else:
            profiles.append(profile)
    return profiles


def workspace_call(request):
    header = {
        'Content-Type': 'application/json'
    }
    auth_token = request.headers.get('Authorization')
    rpc = json.loads(request.body)
    method = rpc['method']
    if auth_token is not None and auth_token == 'bad_token':
        return (500, header, json.dumps({
            'version': '1.1',
            'id': rpc['id'],
            'error': {
                'name': 'JSONRPCError',
                'code': -32001,
                'message': 'INVALID TOKEN'
            }
        }))

    # TODO: emulate permission denied

    # TODO: support the ws methods we do support

    if method == 'Workspace.get_workspace_info':
        result = handle_get_workspace_info(rpc, auth_token)
    else:
        # TODO: make this correct
        return (500, header, json.dumps({
            'version': '1.1',
            'id': rpc['id'],
            'error': {
                'name': 'JSONRPCError',
                'code': -32601,
                'message': f'Method Not Supported "{method}'
            }
        }))

    return (200, header, json.dumps({
        'version': '1.1',
        'id': rpc['id'],
        'result': [result]
    }))


def error_value(code, message):
    return {
        'name': 'JSONRPCError',
        'code': code,
        'message': message
    }


def error_response(request_rpc, error_value):
    header = {
        'Content-Type': 'application/json'
    }
    return_rpc = {
        'version': '1.1',
        'error': error_value
    }
    if 'id' in request_rpc:
        return_rpc['id'] = request_rpc['id']
    return 500, header, json.dumps(return_rpc)


def result_response(request_rpc, result_value):
    header = {
        'Content-Type': 'application/json'
    }
    return_rpc = {
        'version': '1.1',
        'result': result_value
    }
    if 'id' in request_rpc:
        return_rpc['id'] = request_rpc['id']
    return 200, header, json.dumps(return_rpc)


def user_profile_call(request):
    auth_token = request.headers.get('Authorization')
    rpc = json.loads(request.body)
    method = rpc['method']
    if auth_token is not None and auth_token == 'bad_token':
        return error_response(rpc, error_value(-32001, 'INVALID TOKEN'))

    # TODO: emulate permission denied

    # TODO: support the ws methods we do support

    if method == 'UserProfile.get_user_profile':
        result = handle_get_user_profile(rpc, auth_token)
    else:
        # TODO: make this correct
        return error_response(rpc,
                              error_value(-32601, f'Method Not Supported "{method}'))

    return result_response(rpc, [result])
