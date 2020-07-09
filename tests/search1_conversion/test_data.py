
mock_ws_info = [
    1,
    "test_workspace",
    "username",
    "2020-06-06T03:49:55+0000",
    388422,
    "n",
    "r",
    "unlocked",
    {"searchtags": "refdata"}
]

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

test_search_results = {
    'hits': [
        {
            'highlight': {'name': '<em>name1</em>'},
            'doc': {'access_group': 1, 'timestamp': 0, 'name': 'name1'},
            'id': '1',
            'index': 'test_index1_1',
        },
        {
            'highlight': {'name': '<em>name2</em>'},
            'doc': {'access_group': 0, 'timestamp': 0, 'name': 'name2'},
            'id': '1',
            'index': 'test_index1_1',
        },
    ],
    'count': 0,
    'search_time': 1
}

expected_search_results = {
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
            "data": {"name": "name1"},
            "guid": "WS:1/1",
            "kbase_id": "1/1",
            "index_name": "test",
            "type_ver": 0,
            "key_props": {"name": "name1"},
            "highlight": {"name": "<em>name1</em>"}
        },
        {
            "object_name": "",
            "access_group": 0,
            "obj_id": None,
            "version": None,
            "timestamp": 0,
            "type": "",
            "creator": None,
            "data": {"name": "name2"},
            "guid": "WS:1/1",
            "kbase_id": "1/1",
            "index_name": "test",
            "type_ver": 0,
            "key_props": {"name": "name2"},
            "highlight": {"name": "<em>name2</em>"}
        }
    ],
    "access_group_narrative_info": {
        "1": ["", 0, 1591415395, "username", "User Example"]
    },
    "access_groups_info": {
        "1": mock_ws_info,
        "0": mock_ws_info,
    }
}

expected_get_objects = {
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
            "data": {"name": "name1"},
            "guid": "WS:1/1",
            "kbase_id": "1/1",
            "index_name": "test",
            "type_ver": 0,
            "key_props": {"name": "name1"},
            "highlight": {"name": "<em>name1</em>"}
        },
        {
            "object_name": "",
            "access_group": 0,
            "obj_id": None,
            "version": None,
            "timestamp": 0,
            "type": "",
            "creator": None,
            "data": {"name": "name2"},
            "guid": "WS:1/1",
            "kbase_id": "1/1",
            "index_name": "test",
            "type_ver": 0,
            "key_props": {"name": "name2"},
            "highlight": {"name": "<em>name2</em>"}
        }
    ],
    "access_group_narrative_info": {
        "1": ["", 0, 1591415395, "username", "User Example"]
    },
    "access_groups_info": {
        "1": mock_ws_info,
        "0": mock_ws_info
    }
}
