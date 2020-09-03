import os
import subprocess


def setup():
    if os.environ.get("SKIP_DOCKER"):
        return
    # Build and start the app using docker-compose
    file_path = os.path.join('tests', 'docker-compose-ci.yaml')
    cmd = f"docker-compose --file {file_path} up"
    print(f'Running command:\n{cmd}')
    subprocess.Popen(cmd, shell=True)
