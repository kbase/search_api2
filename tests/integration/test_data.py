
# A request to get a total count on refdata for a search query
search_request1 = {
    "id": "xyz",
    "method": "KBaseSearchEngine.search_objects",
    "version": "1.1",
    "params": [{
        "access_filter": {
            "with_private": 0,
            "with_public": 1
        },
        "match_filter": {
            "exclude_subobjects": 1,
            "full_text_in_all": "coli",
            "source_tags": ["refdata"],
            "source_tags_blacklist": 0
        },
        "pagination": {
            "count": 0,
            "start": 0
        },
        "post_processing": {
            "ids_only": 1,
            "include_highlight": 1,
            "skip_data": 1,
            "skip_info": 1,
            "skip_keys": 1
        }
    }]
}

search_response1 = {
    "id": "xyz",
    "jsonrpc": "2.0",
    "result": [{
        "pagination": {
            "start": 0,
            "count": 0
        },
        "sorting_rules": [],
        "objects": [],
        "total": 15039,
        "search_time": 1848
    }]
}

# Method call to get type counts
search_request2 = {
    "version": "1.1",
    "method": "KBaseSearchEngine.search_types",
    "id": "6959719268936883",
    "params": [{
        "access_filter": {
            "with_private": 1,
            "with_public": 1
        },
        "match_filter": {
            "exclude_subobjects": 1,
            "full_text_in_all": "coli",
            "source_tags": ["refdata", "noindex"],
            "source_tags_blacklist": 1
        }
    }]
}

search_response2 = {
    "id": "6959719268936883",
    "jsonrpc": "2.0",
    "result": [{
        "type_to_count": {
            "Narrative": 13,
            "Taxon": 3318,
            "Tree": 3,
            "Genome": 3174,
            "Workspace": 1
        },
        "search_time": 1506
    }]
}
