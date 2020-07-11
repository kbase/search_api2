
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
    # "sorting_rules": [{
    #   "property": "timestamp",
    #   "is_object_property": 0,
    #   "ascending": 1
    # }],
    "objects": [],
    "total": 15039,
    "search_time": 1848
  }]
}
