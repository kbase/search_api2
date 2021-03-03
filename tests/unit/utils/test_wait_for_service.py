from src.utils.wait_for_service import wait_for_service, WAIT_POLL_INTERVAL
import pytest
import logging
import time
import math

# An upper limit on clock time within wait_for_services to make
# a url get call (and other code in that pathway)
MINIMAL_CALL_TIME = 1


def bad_url_with_timeout(name, url, timeout, caplog):
    search2_logger = logging.getLogger('search2')
    # This ensures that logs are propagated and can be captured by caplog
    search2_logger.propagate = True
    with caplog.at_level(logging.INFO, logger='search2'):
        start = time.time()
        with pytest.raises(SystemExit) as se:
            wait_for_service(url, 'foo', timeout=timeout)

        # Ensure it is attempting to exit.
        assert se.type == SystemExit
        assert se.value.code == 1

        # Ensure that the timeout conditions apply:
        # it should have only exited after the timeout has elapsed,
        # but not much longer afterwards, and always  in increments of
        # WAIT_POLL_INTERVAL.
        elapsed = time.time() - start
        assert elapsed > timeout
        max_elapsed = math.ceil(timeout / WAIT_POLL_INTERVAL) * WAIT_POLL_INTERVAL
        assert elapsed < max_elapsed + MINIMAL_CALL_TIME

        # These messages should have been emitted when checking and when
        # failing.
        assert f'Attempting to connect to {name} at {url}' in caplog.text
        assert f'Unable to connect to {name} at {url}' in caplog.text
    search2_logger.propagate = False


def test_init_config_invalid_config_url(caplog):
    bad_url_with_timeout('foo', 'https://foo.bar.baz', 0, caplog)


def test_init_config_invalid_config_url_7_timeout(caplog):
    bad_url_with_timeout('foo', 'https://foo.bar.baz', 7, caplog)


def test_init_config_invalid_config_url_10_timeout(caplog):
    bad_url_with_timeout('foo', 'https://foo.bar.baz', 10, caplog)


def test_init_config_invalid_config_url_12_timeout(caplog):
    bad_url_with_timeout('foo', 'https://foo.bar.baz', 12, caplog)
