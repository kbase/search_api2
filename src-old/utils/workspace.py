"""
Workspace user authentication: find workspaces the user can search
"""
import json
import requests

from src.utils.config import init_config

_CONFIG = init_config()


def ws_auth(auth_token):
    """
    Get a list of workspace IDs that the given username is allowed to access in
    the workspace.
    """
    if not auth_token:
        return []  # anonymous users
    ws_url = _CONFIG['workspace_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspace IDs
    payload = {
        'method': 'Workspace.list_workspace_ids',
        'version': '1.1',
        'params': [{'perm': 'r'}]
    }
    headers = {'Authorization': auth_token}
    resp = requests.post(
        url=ws_url,
        data=json.dumps(payload),
        headers=headers,
    )
    if not resp.ok:
        raise RuntimeError(ws_url, resp.text)
    return resp.json()['result'][0]['workspaces']


def get_workspace_info(workspace_id, auth_token):
    """
    Given a list of workspace ids, return the associated workspace info for each one
    """
    if not auth_token:
        return []  # anonymous users
    ws_url = _CONFIG['workspace_url']
    # TODO session cache this
    # Make a request to the workspace using the user's auth token to find their readable workspace IDs
    payload = {
        'method': 'Workspace.get_workspace_info',
        'version': '1.1',
        'params': [{'id': workspace_id}]
    }
    headers = {'Authorization': auth_token}
    resp = requests.post(
        url=ws_url,
        data=json.dumps(payload),
        headers=headers,
    )
    if not resp.ok:
        raise RuntimeError(ws_url, resp.text)
    result = resp.json()['result']
    if not len(result) > 0:
        raise RuntimeError(ws_url, resp.text)
    return result[0]


def object_info_to_dict(obj_info):
    [id, name, ws_type, saved_date, version, saved_by,
     wsid, wsname, checksum, size, metadata] = obj_info
    return {
        'id': id,
        'name': name,
        'version': version,
        'type': ws_type,
        'saved_date': saved_date,
        'saved_by': saved_by,
        'workspace_id': wsid,
        'workspace_name': wsname,
        'checksum': checksum,
        'size': size,
        'metadata': metadata
    }


def workspace_info_to_dict(ws_info):
    [id, name, owner, moddate, max_objid, user_permission,
     global_permission, lockstat, metadata] = ws_info
    return {
        'id': id,
        'name': name,
        'owner': owner,
        'modification_date': moddate,
        'max_object_id': max_objid,
        'user_permission': user_permission,
        'global_permission': global_permission,
        'lock_status': lockstat,
        'metadata': metadata
    }
