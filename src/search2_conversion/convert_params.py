

def search_workspace(params, meta):
    """
    Convert parameters from the client into a format that can be passed into
    the es_client.search function
    """
    converted = {
        "query": {
        }
    }
    if "access" in params:
        converted["only_public"] = bool(params["access"].get("only_public"))
        converted["only_private"] = bool(params["access"].get("only_private"))
    converted["track_total_hits"] = bool(params["track_total_hits"])
    if "sorts" in params:
        converted["sort"] = []
        for sort in params.get("sorts"):
            fieldname = sort[0]
            direction = sort[1]
            converted["sort"].append({fieldname: {"order": direction}})
    if "search" in params:
        query = params["search"]["query"]
        fields = params["search"]["fields"]
        converted["query"]["simple_query_string"] = {
            "fields": fields,
            "query": query
        }
    if "filters" in params:
        params["query"]["bool"] = _convert_filters(params['filters'])
    # TODO convert "filters"
    return params


def _convert_filters(filters):
    if 'operator' in filters:
        # We have a filter clause
        if filters['operator'] == 'AND':
            return {
                "must": [
                    _convert_filters(f) for f in filters['fields']
                ]
            }
        else:
            return {
                "should": [
                    _convert_filters(f) for f in filters['fields']
                ]
            }
    elif "term" in filters:
        return {"term": {filters["field"]: {"value": filters["term"]}}}
    elif "not_term" in filters:
        return {
            "must_not": {
                "term": {filters["field"]: {"value": filters["term"]}}
            }
        }
    elif "range" in filters:
        # Convert the range claus into ES syntax
        # Eg, given: {"range": {"min": 10, "max": 11}, "field": "x"}
        #   returns: {"range": {"x": {"gte": 10, "lte": 11}}
        field = filters["field"]
        ret = {"range": {field: {}}}
        if "max" in filters["range"]:
            ret["range"][field]["lte"] = filters["range"]["max"]
        if "min" in filters["range"]:
            ret["range"][field]["gte"] = filters["range"]["min"]
        return ret
