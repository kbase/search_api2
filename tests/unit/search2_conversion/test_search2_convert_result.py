from src.search2_conversion import convert_result


def test_search2_convert_result_valid():
    """Basic test."""
    result = {
        "search_time": 10,
        "count": 11,
        "hits": [{"doc": "hi"}, {"doc": "there"}],
    }
    params = {}
    meta = {}
    converted = convert_result.search_workspace(result, params, meta)
    assert converted["search_time"] == result["search_time"]
    assert converted["count"] == result["count"]
    assert converted["hits"] == ["hi", "there"]
