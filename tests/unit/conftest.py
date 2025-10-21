# content of a/conftest.py
import os
# Set environment variables BEFORE any other imports
# This ensures the config module picks up the auth credentials
os.environ['ELASTICSEARCH_URL'] = 'http://localhost:9200'
os.environ['ELASTICSEARCH_AUTH_USERNAME'] = 'elastic'
os.environ['ELASTICSEARCH_AUTH_PASSWORD'] = 'changeme'

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
