from src.utils.config import init_config, auth_header_encoder
import os
import pytest


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


@pytest.mark.parametrize("username,password", [
    (None, None),
    (None, 'password'),
    ('username', None),
    ('', ''),
    ('', 'password'),
    ('username', ''),
])
def test_auth_header_encoder_missing_credentials(username, password):
    with pytest.raises(RuntimeError, match="Elasticsearch authentication credentials are required"):
        auth_header_encoder(username, password)
