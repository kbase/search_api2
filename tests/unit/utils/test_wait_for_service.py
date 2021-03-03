from src.utils.wait_for_service import wait_for_service, WAIT_POLL_INTERVAL
import pytest
import logging
import time

MINIMAL_CALL_TIME = 1


def test_init_config_invalid_config_url(caplog):
    search2_logger = logging.getLogger('search2')
    # This ensures that logs are propagated and can be captured by caplog
    search2_logger.propagate = True
    with caplog.at_level(logging.INFO, logger='search2'):
        start = time.time()
        with pytest.raises(SystemExit) as se:
            wait_for_service('https://foo.bar.baz', 'foo', timeout=0)
        assert se.type == SystemExit
        assert se.value.code == 1
        # If it took less than 5 seconds, we triggered the exit
        # on the first check in the while loop.
        elapsed = time.time() - start
        assert elapsed < MINIMAL_CALL_TIME
        assert 'Attempting to connect to foo at https://foo.bar.baz' in caplog.text
        assert 'Unable to connect to foo at https://foo.bar.baz' in caplog.text
    search2_logger.propagate = False


def test_init_config_invalid_config_url_longer_timeout(caplog):
    search2_logger = logging.getLogger('search2')
    # This ensures that logs are propagated and can be captured by caplog
    search2_logger.propagate = True
    with caplog.at_level(logging.INFO, logger='search2'):
        start = time.time()
        with pytest.raises(SystemExit) as se:
            wait_for_service('https://foo.bar.baz', 'foo', timeout=10)
        assert se.type == SystemExit
        assert se.value.code == 1
        # If it took less than 5 seconds, we triggered the exit
        # on the first check in the while loop.
        elapsed = time.time() - start
        assert elapsed > 10
        assert elapsed < 10 + MINIMAL_CALL_TIME
        assert 'Attempting to connect to foo at https://foo.bar.baz' in caplog.text
        assert 'Unable to connect to foo at https://foo.bar.baz' in caplog.text
    search2_logger.propagate = False
