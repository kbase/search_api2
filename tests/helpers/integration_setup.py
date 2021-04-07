import subprocess
import signal
from src.utils.wait_for_service import wait_for_service
from src.utils.logger import logger
import json
import os
import requests
from . import common
from .common import assert_jsonrpc11_result, equal

container_process = None
container_out = None
container_err = None
stop_timeout = 30


def start_service(app_url):
    global container_process
    global container_out
    global container_err

    # Build and start the app using docker-compose
    cwd = 'tests/integration/docker'
    logger.info(f'Running docker-compose file in "{cwd}"')
    cmd = "docker-compose --no-ansi up"
    logger.info(f'Running command:\n{cmd}')
    container_out = open("container.out", "w")
    container_err = open("container.err", "w")
    container_process = subprocess.Popen(cmd, shell=True,
                                         stdout=container_out,
                                         stderr=container_err,
                                         cwd=cwd)
    wait_for_service(app_url, "search2")


def stop_service():
    global container_process
    global container_out
    global container_err

    if container_process is not None:
        logger.info('Stopping container')
        container_process.send_signal(signal.SIGTERM)
        logger.info('Waiting until service has stopped...')

        if not common.wait_for_line("container.err",
                                    lambda line: 'Stopping' in line and 'done' in line,
                                    timeout=stop_timeout,
                                    line_count=1):
            raise Exception(f'Container did not stop in the alloted time of {stop_timeout} seconds')
        logger.info('...stopped!')

    if container_err is not None:
        container_err.close()

    if container_out is not None:
        container_out.close()


def load_data_file(method, name):
    """Load the json test data file with the given name from ./data/legacy """
    file_path = os.path.join(os.path.dirname(__file__), '../integration/data/legacy', method, name)
    logger.info(f'loading data file from "{file_path}"')
    with open(file_path) as f:
        return json.load(f)


def do_rpc(url, request_data, response_data):
    """Send the given jsonrpc request, do basic jsonrpc 1.1 compliance check."""
    resp = requests.post(
        url=url,
        headers={'Authorization': os.environ['WS_TOKEN']},
        data=json.dumps(request_data),
    )
    return assert_jsonrpc11_result(resp.json(), response_data)


def assert_equal_results(actual_result, expected_result):
    """Asserts that the actual results match expected; omits non-deterministic fields"""
    for key in ['pagination', 'sorting_rules', 'total', 'objects']:
        assert equal(actual_result[key], expected_result[key])

    # Optional keys (may be enabled, or not)
    # We check if the specified keys are expected, and matching,
    # or present, and expected.

    for key in ['access_group_narrative_info', 'access_group_narrative_info']:
        # here we check only if it is in our expected result.
        if key in expected_result:
            assert equal(actual_result[key], expected_result[key])

    for key in ['access_group_narrative_info', 'access_group_narrative_info']:
        # but here we check if is in the actual result.
        if key in actual_result:
            assert equal(actual_result[key], expected_result[key])
