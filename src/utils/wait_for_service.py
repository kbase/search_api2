import requests
import time

from src.utils.logger import logger

DEFAULT_TIMEOUT = 180
WAIT_POLL_INTERVAL = 5


def wait_for_service(url, name, timeout=DEFAULT_TIMEOUT):
    start = time.time()
    while True:
        logger.info(f'Attempting to connect to {name} at {url}')
        try:
            requests.get(url, timeout=timeout).raise_for_status()
            logger.info(f'{name} is online!')
            break
        except Exception:
            logger.info(f'Waiting for {name} at {url}')
            total_elapsed = time.time() - start
            if total_elapsed > timeout:
                logger.error(f'Unable to connect to {name} at {url} after {total_elapsed} seconds')
                exit(1)
            time.sleep(WAIT_POLL_INTERVAL)
