"""
Integration tests for Elasticsearch authentication.

These tests verify that the search API can successfully connect to and query
an Elasticsearch instance with authentication enabled (using the docker-compose setup).
"""
import requests
from src.utils.config import config


def test_elasticsearch_requires_auth(services):
    """Test that Elasticsearch requires authentication (rejects requests without auth)."""
    es_url = config['elasticsearch_url']
    resp_no_auth = requests.get(es_url)
    assert resp_no_auth.status_code == 401, \
        f"Elasticsearch should require authentication, got status {resp_no_auth.status_code}"


def test_elasticsearch_with_auth(services):
    """Test that Elasticsearch accepts requests with proper authentication."""
    es_url = config['elasticsearch_url']
    headers = {}
    auth_header_value = config['authorization_header_value']
    if auth_header_value:
        headers['Authorization'] = auth_header_value
    resp_with_auth = requests.get(es_url, headers=headers)
    assert resp_with_auth.status_code == 200, \
        f"Elasticsearch should accept authenticated requests, got status {resp_with_auth.status_code}"
