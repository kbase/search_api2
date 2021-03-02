from src.utils.wait_for_service import wait_for_service
import pytest
import logging
import time


def test_init_config_invalid_config_url(caplog):
    search2_logger = logging.getLogger('search2')
    # This ensures that logs are propagated and can be captured by caplog
    search2_logger.propagate = True
    with caplog.at_level(logging.INFO, logger='search2'):
        with pytest.raises(SystemExit) as se:
            wait_for_service('https://foo.bar.baz', 'foo', timeout=0)
        start = time.time()
        assert se.type == SystemExit
        assert se.value.code == 1
        # If it took less than 10 seconds, we triggered the exist on timeout
        # on the first check.
        assert time.time() - start < 5
        assert 'Attempting to connect to foo at https://foo.bar.baz' in caplog.text
        assert 'Unable to connect to foo at https://foo.bar.baz' in caplog.text
    search2_logger.propagate = False
