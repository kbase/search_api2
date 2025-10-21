import subprocess
from src.utils.wait_for_service import wait_for_service
from src.utils.logger import logger
import json
import os


container_process = None
container_out = None
container_err = None
stop_timeout = 30


def load_data_file(name):
    """Load the json test data file with the given name from ./data/legacy """
    file_path = os.path.join(os.path.dirname(__file__), '../unit/data', name)
    logger.info(f'loading data file from "{file_path}"')
    with open(file_path) as f:
        return json.load(f)


def start_service(wait_for_url, wait_for_name):
    global container_process
    global container_out
    global container_err

    # Set environment variables BEFORE importing config module
    # This ensures config picks up the auth credentials
    os.environ['ELASTICSEARCH_URL'] = 'http://localhost:9200'
    os.environ['ELASTICSEARCH_AUTH_USERNAME'] = 'elastic'
    os.environ['ELASTICSEARCH_AUTH_PASSWORD'] = 'changeme'

    cmd = "docker compose --ansi never up"
    logger.info(f'Running command:\n{cmd}')
    container_out = open("container.out", "w")
    container_err = open("container.err", "w")
    container_process = subprocess.Popen(cmd, shell=True, stdout=container_out, stderr=container_err)
    wait_for_service(wait_for_url, wait_for_name)


def stop_service():
    if container_process is not None:
        logger.info('Stopping container')

        # Stop and remove containers
        subprocess.run("docker compose --ansi never down", shell=True, check=True)
        logger.info('Service has stopped!')

    if container_err is not None:
        container_err.close()

    if container_out is not None:
        container_out.close()
