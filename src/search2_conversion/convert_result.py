

def search_workspace(results, params, meta):
    """
    Return result data from es_client.query and convert into a format
    conforming to the schema found in
    rpc-methods.yaml/definitions/methods/search_workspace/result
    """
    return {
        "search_time": results["search_time"],
        "count": results["count"],
        "hits": [hit["doc"] for hit in results["hits"]],
    }
