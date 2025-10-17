from src.utils.config import init_config, get_elasticsearch_auth_header
import os
import pytest
import base64
from unittest.mock import patch


def test_init_config_invalid_config_url():
    original_url = os.environ.get('GLOBAL_CONFIG_URL')
    os.environ['GLOBAL_CONFIG_URL'] = "foo://bar"
    with pytest.raises(RuntimeError) as rte:
        init_config()
    assert 'Invalid config url: foo://bar' in str(rte)
    if original_url is not None:
        os.environ['GLOBAL_CONFIG_URL'] = original_url
    else:
        os.environ.pop('GLOBAL_CONFIG_URL')


@patch('src.utils.config.config')
def test_get_elasticsearch_auth_header_basic_auth(mock_config):
    """Test Basic authentication when username and password are set."""
    mock_config.get.side_effect = lambda key: {
        'elasticsearch_auth_username': 'testuser',
        'elasticsearch_auth_password': 'testpass',
        'elasticsearch_auth_token': None
    }.get(key)

    auth_header = get_elasticsearch_auth_header()

    # Verify Basic auth format
    assert auth_header.startswith('Basic ')

    # Verify the credentials are properly base64 encoded
    encoded_part = auth_header.split(' ')[1]
    decoded = base64.b64decode(encoded_part).decode('utf-8')
    assert decoded == 'testuser:testpass'


@patch('src.utils.config.config')
def test_get_elasticsearch_auth_header_bearer_auth(mock_config):
    """Test Bearer authentication when only token is set."""
    mock_config.get.side_effect = lambda key: {
        'elasticsearch_auth_username': None,
        'elasticsearch_auth_password': None,
        'elasticsearch_auth_token': 'my-secret-token'
    }.get(key)

    auth_header = get_elasticsearch_auth_header()

    # Verify Bearer auth format
    assert auth_header == 'Bearer my-secret-token'


@patch('src.utils.config.config')
def test_get_elasticsearch_auth_header_no_auth(mock_config):
    """Test that None is returned when no credentials are set."""
    mock_config.get.side_effect = lambda key: {
        'elasticsearch_auth_username': None,
        'elasticsearch_auth_password': None,
        'elasticsearch_auth_token': None
    }.get(key)

    auth_header = get_elasticsearch_auth_header()

    # Verify no auth header is returned
    assert auth_header is None


@patch('src.utils.config.config')
def test_get_elasticsearch_auth_header_basic_priority(mock_config):
    """Test that Basic auth takes priority when both username/password and token are set."""
    mock_config.get.side_effect = lambda key: {
        'elasticsearch_auth_username': 'testuser',
        'elasticsearch_auth_password': 'testpass',
        'elasticsearch_auth_token': 'my-token'
    }.get(key)

    auth_header = get_elasticsearch_auth_header()

    # Verify Basic auth is used (has priority)
    assert auth_header.startswith('Basic ')


@patch('src.utils.config.config')
def test_get_elasticsearch_auth_header_partial_basic(mock_config):
    """Test that Bearer auth is used when only username OR password is set (not both)."""
    mock_config.get.side_effect = lambda key: {
        'elasticsearch_auth_username': 'testuser',
        'elasticsearch_auth_password': None,
        'elasticsearch_auth_token': 'my-token'
    }.get(key)

    auth_header = get_elasticsearch_auth_header()

    # Should fall back to Bearer auth since password is missing
    assert auth_header == 'Bearer my-token'
