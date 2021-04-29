import json
import requests


def test_narrative_example(service):
    params = {
        "access": {
            "only_public": True,
        },
        "types": ["KBaseGenomes.Genome"],
        "search": {
            "query": "escherichia coli",
            "fields": ["agg_fields", "scientific_name"]
        },
        "filters": {
            "field": "tags", "term": "refdata"
        },
        "paging": {
            "length": 10,
            "offset": 0
        }
    }
    url = service['app_url'] + '/rpc'
    resp = requests.post(
        url=url,
        data=json.dumps({
            "method": "search_workspace",
            "jsonrpc": "2.0",
            "id": 0,
            "params": params
        })
    )
    data = resp.json()
    assert 'result' in data
    assert data['result']['count'] > 0


def test_dashboard_example(service):
    params = {
        "id": 1597353298754,
        "jsonrpc": "2.0",
        "method": "search_workspace",
        "params": {
            "filters": {
                "fields": [
                  {"field": "creator", "term": "kbaseuitest"}
                ],
                "operator": "AND"
            },
            "paging": {"length": 20, "offset": 0},
            "sorts": [["timestamp", "desc"], ["_score", "desc"]],
            "track_total_hits": False,
            "types": ["KBaseNarrative.Narrative"]
        }
    }
    url = service['app_url'] + '/rpc'
    resp = requests.post(
        url=url,
        data=json.dumps(params),
    )
    data = resp.json()
    assert 'result' in data
    assert data['result']['count'] > 0
