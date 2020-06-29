import requests
import time

from src.utils.logger import logger


def wait_for_service(url, name, timeout=180):
    start = time.time()
    while True:
        logger.info(f'Attempting to connect to {name} at {url}')
        try:
            requests.get(url).raise_for_status()
            logger.info(f'{name} is online!')
            break
        except Exception:
            logger.info(f'Waiting for {name} at {url}')
            if time.time() - start > timeout:
                logger.error(f'Unable to connect to {name} at {url}')
                exit(1)
            time.sleep(5)
