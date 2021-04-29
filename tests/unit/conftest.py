# content of a/conftest.py
import pytest
from tests.helpers.unit_setup import (
    start_service,
    stop_service
)
from tests.helpers import init_elasticsearch

# ES_URL = 'http://localhost:9200'
APP_URL = 'http://localhost:5000'


@pytest.fixture(scope="session")
def services():
    start_service(APP_URL, 'searchapi2')
    init_elasticsearch()
    yield {'app_url': APP_URL}
    stop_service()
