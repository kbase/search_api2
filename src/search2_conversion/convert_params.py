from src.utils.config import config
from src.exceptions import UnknownType


def search_workspace(params, meta):
    """
    Convert parameters from the client into a format that can be passed into
    the es_client.search function
    """
    # Initialize the result of this function
    converted = {"query": {"bool": {"must": []}}}
    if "access" in params:
        converted["only_public"] = bool(params["access"].get("only_public"))
        converted["only_private"] = bool(params["access"].get("only_private"))
    converted["track_total_hits"] = bool(params.get("track_total_hits"))
    if "types" in params:
        # Get the index names from KBase type names using global config data
        indexes = []
        # TODO allow for both unversioned and version type filtering here
        mapping = config['global']['ws_type_to_indexes']
        for typ in params['types']:
            if typ not in mapping:
                available = list(mapping.keys())
                msg = f"Unknown type: {type}. Available types: {available}."
                raise UnknownType(msg)
            indexes.append(mapping[typ])
        converted["indexes"] = indexes
    if "types" not in params or len(params["types"]) == 0:
        indexes = list(config['global']['ws_type_to_indexes'].values())
        converted["indexes"] = indexes
    if "sorts" in params:
        # Convert from our format into Elasticsearch's format
        # [[field, dir]] -> [{field: {'order': dir}}]
        converted["sort"] = []
        for sort in params.get("sorts"):
            fieldname = sort[0]
            direction = sort[1]
            converted["sort"].append({fieldname: {"order": direction}})
    if "search" in params:
        # Elasticsearch Simple Query String
        query = params["search"]["query"]
        fields = params["search"].get("fields", ['agg_fields'])
        converted["query"]["bool"]["must"].append({
            "simple_query_string": {
                "fields": fields,
                "query": query,
                "default_operator": "AND",
            }
        })
    if "filters" in params:
        converted_query = _convert_filters(params['filters'])
        converted["query"]["bool"]["must"].append(converted_query)
    paging = params.get('paging', {})
    converted['from'] = paging.get('offset', 0)
    converted['size'] = paging.get('length', 10)
    return converted


def _convert_filters(filters):
    if 'operator' in filters:
        # We have a filter clause
        if filters['operator'] == 'AND':
            # Recursive call for sub-clauses
            return {
                "bool": {
                    "must": [
                        _convert_filters(f) for f in filters['fields']
                    ]
                }
            }
        else:
            # Recursive call for sub-clauses
            return {
                "bool": {
                    "should": [
                        _convert_filters(f) for f in filters['fields']
                    ]
                }
            }
    elif "term" in filters:
        # Base case term match
        return {"term": {filters["field"]: {"value": filters["term"]}}}
    elif "not_term" in filters:
        # Base case negated term match
        return {
            "bool": {
                "must_not": {
                    "term": {filters["field"]: {"value": filters["not_term"]}}
                }
            }
        }
    elif "range" in filters:
        # Base case range filter
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
