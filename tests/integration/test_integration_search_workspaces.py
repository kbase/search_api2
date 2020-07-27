import json
import os
import requests

from tests.helpers.integration_setup import setup
from src.utils.wait_for_service import wait_for_service


APP_URL = os.environ.get("APP_URL", 'http://localhost:5000')
setup()

# This implicitly tests the "/" path
wait_for_service(APP_URL, "search2")


def test_narrative_example():
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
            "field": "source", "term": "refseq"
        },
        "paging": {
            "length": 10,
            "offset": 0
        }
    }
    url = APP_URL + '/rpc'
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
    print("DATA", data)
