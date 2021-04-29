
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
                'obj_type_name': 'Type',
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
                'obj_type_name': 'Type',
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
    # public workspace, refdata
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
    # public workspace, narrative
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
    ],
    # private workspace, narrative
    "100": [
        100,
        "workspace100",
        "username",
        "2020-01-02T03:04:05+0000",
        388422,
        "r",
        "n",
        "unlocked",
        {
            "searchtags": "narrative",
            "narrative": "1",
            "narrative_nice_name": "narrative 100",
            "is_temporary": "f"
        }
    ],
    # private, inaccessible workspace, narrative
    "101": [
        101,
        "workspace101",
        "username",
        "2020-01-02T03:04:05+0000",
        388422,
        "n",
        "n",
        "unlocked",
        {
            "searchtags": "narrative",
            "narrative": "1",
            "narrative_nice_name": "narrative 101",
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
            "id": "WS::1:2",
            "object_name": "object2",
            "workspace_id": 1,
            "object_id": 2,
            "object_version": 1,
            "modified_at": 0,
            "workspace_type_name": "Type",
            "creator": "username",
            "data": {"name": "name1"},
            "index_name": "test",
            "index_version": 0,
            "highlight": {"name": "<em>name1</em>"}
        },
        {
            "id": "WS::0:2",
            "object_name": "object2",
            "workspace_id": 0,
            "object_id": 2,
            "object_version": 1,
            "modified_at": 0,
            "workspace_type_name": "Type",
            "creator": "username",
            "data": {"name": "name2"},
            "index_name": "test",
            "index_version": 0,
            "highlight": {"name": "<em>name2</em>"}
        }
    ],
    "access_group_narrative_info": {
        '1': ['narrative1', 1, 1577934245000, 'username', 'User Example']
    },
    "access_groups_info": {
        # public workspace, refdata
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
        # public workspace, narrative
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
}

expected_get_objects = {
    "search_time": 1,
    "objects": [
        {
            "id": "WS::1:2",
            "object_name": "object2",
            "workspace_id": 1,
            "object_id": 2,
            "object_version": 1,
            "modified_at": 0,
            "workspace_type_name": "Type",
            "creator": "username",
            "data": {"name": "name1"},
            "index_name": "test",
            "index_version": 0,
            "highlight": {"name": "<em>name1</em>"}
        },
        {
            "id": "WS::0:2",
            "object_name": "object2",
            "workspace_id": 0,
            "object_id": 2,
            "object_version": 1,
            "modified_at": 0,
            "workspace_type_name": "Type",
            "creator": "username",
            "data": {"name": "name2"},
            "index_name": "test",
            "index_version": 0,
            "highlight": {"name": "<em>name2</em>"}
        }
    ],
    "access_group_narrative_info": {
        '1': ['narrative1', 1, 1577934245000, 'username', 'User Example']
    },
    "access_groups_info": {
        # public workspace, refdata
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
        # public workspace, narrative
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
}
