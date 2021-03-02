# content of a/conftest.py
import pytest
import os
from tests.helpers.integration_setup import (
    start_service,
    stop_service
)

APP_URL = os.environ.get("APP_URL", 'http://localhost:5000')


@pytest.fixture(scope="session")
def service():
    start_service(APP_URL)
    yield {'app_url': APP_URL}
    stop_service()
