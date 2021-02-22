
# This test data simulates a search space of two objects across two
# narratives.

# Raw results
test_search_results = {
    'hits': [
        {
            'highlight': {'name': '<em>name1</em>'},
            'doc': {
                'access_group': 1,
                'creator': 'username',
                'obj_id': 2,
                'obj_name': 'object2',
                'version': 1,
                'obj_type_name': 'Module.Type-1.0',
                'timestamp': 0,
                'name': 'name1'
            },
            'id': 'WS::1:2',
            'index': 'test_index1_1',
        },
        {
            'highlight': {'name': '<em>name2</em>'},
            'doc': {
                'access_group': 0,
                'creator': 'username',
                'obj_id': 2,
                'obj_name': 'object2',
                'version': 1,
                'obj_type_name': 'Module.Type-1.0',
                'timestamp': 0,
                'name': 'name2'
            },
            'id': 'WS::0:2',
            'index': 'test_index1_1',
        },
    ],
    'count': 0,
    'search_time': 1
}

mock_ws_info = {
    "0": [
        0,
        "workspace0",
        "username",
        "2020-01-02T03:04:05+0000",
        388422,
        "n",
        "r",
        "unlocked",
        {
            "searchtags": "refdata"
        }
    ],
    "1": [
        1,
        "workspace1",
        "username",
        "2020-01-02T03:04:05+0000",
        388422,
        "n",
        "r",
        "unlocked",
        {
            "searchtags": "narrative",
            "narrative": "1",
            "narrative_nice_name": "narrative1",
            "is_temporary": "f"
        }
    ]
}

# object_info is:
# object id, object name, workspace type, date saved, version,
# saved by, workspace id, workspace name, checksum, size, metadata
mock_object_info = [[
    2,                 # object id
    "object2",         # object name
    "Module.Type-1.0",  # workspace type
    1000,              # saved time
    1,                 # version
    "username",           # saved by
    0,                 # workspace id
    "workspace0",      # workspace name
    "ab123",           # checksum
    123,               # size
    {

    }
],
    [
        2,                 # object id
        "object2",         # object name
        "Module.Type-1.0",  # workspace type
        1000,              # saved time
        1,                 # version
        "username",           # saved by
        1,                 # workspace id
        "workspace1",      # workspace name
        "ab123",           # checksum
        123,               # size
        {

        }
]]

mock_user_profiles = [{
    "user": {
        "username": "username",
        "realname": "User Example"
    },
    "profile": {
        "metadata": {
            "createdBy": "userprofile_ui_service",
            "created": "2018-06-06T17:28:20.964Z"
        },
        "preferences": {},
        "userdata": {
            "organization": "Org",
            "department": "Dept",
            "city": "Berkeley",
            "state": "California",
            "postalCode": "94703",
            "country": "United States",
            "researchStatement": "Research Statement",
            "researchInterests": [],
            "affiliations": [],
            "fundingSource": "USDA - Forest Service (FS)",
            "gravatarDefault": "2",
            "avatarOption": "0",
            "jobTitle": "CEO"
        },
        "synced": {"gravatarHash": "f5566303ee95cf08cdfc0cc21dc74707"},
        "plugins": {},
    }
}]


expected_search_results = {
    "pagination": {},
    "sorting_rules": [],
    "total": 0,
    "search_time": 1,
    "objects": [
        {
            "object_name": "object2",
            "access_group": 1,
            "obj_id": 2,
            "version": 1,
            "timestamp": 0,
            "type": "Module.Type-1.0",
            "creator": "username",
            "data": {"name": "name1"},
            "guid": "WS:1/2/1",
            "kbase_id": "1/2/1",
            "index_name": "test",
            "type_ver": 0,
            "highlight": {"name": "<em>name1</em>"}
        },
        {
            "object_name": "object2",
            "access_group": 0,
            "obj_id": 2,
            "version": 1,
            "timestamp": 0,
            "type": "Module.Type-1.0",
            "creator": "username",
            "data": {"name": "name2"},
            "guid": "WS:0/2/1",
            "kbase_id": "0/2/1",
            "index_name": "test",
            "type_ver": 0,
            "highlight": {"name": "<em>name2</em>"}
        }
    ],
    "access_group_narrative_info": {
        '1': ['narrative1', 1, 1577934245000, 'username', 'User Example']
    },
    "access_groups_info": mock_ws_info
}

expected_get_objects = {
    "search_time": 1,
    "objects": [
        {
            "object_name": "object2",
            "access_group": 1,
            "obj_id": 2,
            "version": 1,
            "timestamp": 0,
            "type": "Module.Type-1.0",
            "creator": "username",
            "data": {"name": "name1"},
            "guid": "WS:1/2/1",
            "kbase_id": "1/2/1",
            "index_name": "test",
            "type_ver": 0,
            "highlight": {"name": "<em>name1</em>"}
        },
        {
            "object_name": "object2",
            "access_group": 0,
            "obj_id": 2,
            "version": 1,
            "timestamp": 0,
            "type": "Module.Type-1.0",
            "creator": "username",
            "data": {"name": "name2"},
            "guid": "WS:0/2/1",
            "kbase_id": "0/2/1",
            "index_name": "test",
            "type_ver": 0,
            "highlight": {"name": "<em>name2</em>"}
        }
    ],
    "access_group_narrative_info": {
        '1': ['narrative1', 1, 1577934245000, 'username', 'User Example']
    },
    "access_groups_info": mock_ws_info
}
