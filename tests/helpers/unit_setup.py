import subprocess
import signal
from src.utils.wait_for_service import wait_for_service
from src.utils.logger import logger
from . import common


container_process = None
container_out = None
container_err = None
stop_timeout = 30


def start_service(wait_for_url, wait_for_name):
    global container_process
    global container_out
    global container_err

    cmd = "docker-compose --no-ansi up"
    logger.info(f'Running command:\n{cmd}')
    container_out = open("container.out", "w")
    container_err = open("container.err", "w")
    container_process = subprocess.Popen(cmd, shell=True, stdout=container_out, stderr=container_err)
    wait_for_service(wait_for_url, wait_for_name)


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
                                    line_count=2):
            raise Exception(f'Container did not stop in the alloted time of {stop_timeout} seconds')
        logger.info('...stopped!')

    if container_err is not None:
        container_err.close()

    if container_out is not None:
        container_out.close()
