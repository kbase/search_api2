import os
import pytest
import base64


from src.utils.config import init_config, auth_header_encoder


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


def test_auth_header_encoder_valid_credentials():
    """
    Tests if the function correctly encodes a valid username and password.
    """
    username = "testuser"
    password = "testpassword123"

    # Manually create the expected Base64 string for verification
    expected_credentials = base64.b64encode(b"testuser:testpassword123").decode('utf-8')
    expected_header = f"Basic {expected_credentials}"

    assert auth_header_encoder(username, password) == expected_header


@pytest.mark.parametrize(
    "username, password",
    [
        (None, "password"),  # No username
        ("username", None),  # No password
        ("", "password"),  # Empty username
        ("username", ""),  # Empty password
        (None, None),  # Both None
        ("", ""),  # Both empty
    ],
)
def test_auth_header_encoder_missing_credentials_returns_none(username, password):
    """
    Tests if the function returns None when username or password is not provided.
    """
    assert auth_header_encoder(username, password) is None


def test_auth_header_encoder_with_special_characters():
    """
    Tests if the function correctly handles credentials with special characters.
    """
    username = "user@example.com"
    password = "p@$$w*rd!"

    credentials_str = f"{username}:{password}"
    expected_credentials = base64.b64encode(credentials_str.encode('utf-8')).decode('utf-8')
    expected_header = f"Basic {expected_credentials}"

    assert auth_header_encoder(username, password) == expected_header
