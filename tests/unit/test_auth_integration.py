"""
Integration tests for Elasticsearch authentication.

These tests verify that the search API can successfully connect to and query
an Elasticsearch instance with authentication enabled (using the docker-compose setup).
"""
import requests
from src.utils.config import config, get_elasticsearch_auth_header


def test_elasticsearch_requires_auth(services):
    """Test that Elasticsearch requires authentication (rejects requests without auth)."""
    es_url = config['elasticsearch_url']

    # Test without auth - should fail with 401
    resp_no_auth = requests.get(es_url)
    assert resp_no_auth.status_code == 401, \
        f"Elasticsearch should require authentication, got status {resp_no_auth.status_code}"


def test_elasticsearch_accepts_valid_auth(services):
    """Test that Elasticsearch accepts valid authentication credentials."""
    es_url = config['elasticsearch_url']
    es_username = config.get('elasticsearch_auth_username', 'elastic')
    es_password = config.get('elasticsearch_auth_password', 'changeme')

    # Test with auth - should succeed
    resp_with_auth = requests.get(es_url, auth=(es_username, es_password))
    assert resp_with_auth.status_code == 200, \
        f"Elasticsearch should accept valid credentials, got status {resp_with_auth.status_code}"

    # Verify the response contains expected cluster info
    data = resp_with_auth.json()
    assert 'cluster_name' in data, "Response should contain cluster_name"
    assert 'version' in data, "Response should contain version info"


def test_get_elasticsearch_auth_header_returns_basic_auth(services):
    """Test that get_elasticsearch_auth_header returns Basic auth when credentials are configured."""
    auth_header = get_elasticsearch_auth_header()

    # Should return Basic auth header
    assert auth_header is not None, "Auth header should not be None"
    assert auth_header.startswith('Basic '), f"Expected Basic auth, got: {auth_header}"


def test_elasticsearch_create_index_with_auth(services):
    """Test that we can create an index on auth-enabled Elasticsearch."""
    es_url = config['elasticsearch_url']
    test_index_name = f"{config['index_prefix']}{config['prefix_delimiter']}auth_test_index"

    # Get auth header using the centralized function
    auth_header = get_elasticsearch_auth_header()
    headers = {'Content-Type': 'application/json'}
    if auth_header:
        headers['Authorization'] = auth_header

    # Clean up if index exists
    requests.delete(f"{es_url}/{test_index_name}", headers=headers)

    # Create index
    resp = requests.put(
        f"{es_url}/{test_index_name}",
        json={'settings': {'index': {'number_of_shards': 1, 'number_of_replicas': 0}}},
        headers=headers
    )

    assert resp.status_code in [200, 201], \
        f"Failed to create index with auth: {resp.status_code} - {resp.text}"

    # Verify index exists
    resp_check = requests.head(f"{es_url}/{test_index_name}", headers=headers)
    assert resp_check.status_code == 200, "Index should exist after creation"

    # Clean up
    requests.delete(f"{es_url}/{test_index_name}", headers=headers)


def test_elasticsearch_rejects_invalid_auth(services):
    """Test that Elasticsearch rejects invalid authentication credentials."""
    es_url = config['elasticsearch_url']

    # Test with wrong credentials - should fail with 401
    resp_bad_auth = requests.get(es_url, auth=('wrong_user', 'wrong_password'))
    assert resp_bad_auth.status_code == 401, \
        f"Elasticsearch should reject invalid credentials, got status {resp_bad_auth.status_code}"
