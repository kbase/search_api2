# content of a/conftest.py
import pytest
import os
from tests.helpers.integration_setup import (
    start_service,
    stop_service
)


DEFAULT_APP_URL = 'http://localhost:5000'

APP_URL = os.environ.get("APP_URL", DEFAULT_APP_URL)


@pytest.fixture(scope="session")
def service():
    if APP_URL == DEFAULT_APP_URL:
        start_service(APP_URL)
    yield {'app_url': APP_URL}
    if APP_URL == DEFAULT_APP_URL:
        stop_service()
