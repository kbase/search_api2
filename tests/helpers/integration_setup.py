import os
import subprocess


def setup():
    if os.environ.get("SKIP_DOCKER"):
        return
    ES_URL = os.environ.get("ES_URL", "http://localhost:9500")
    # TOKEN = os.environ["TOKEN"]
    INDEX_PREFIX = os.environ.get('INDEX_PREFIX', 'search2')
    USER_PROFILE_URL = os.environ.get('USER_PROFILE_URL', 'https://ci.kbase.us/services/user_profile')
    WS_URL = os.environ.get('WS_URL', 'https://ci.kbase.us/services/ws')
    IMAGE_NAME = "kbase/search2"
    # Build and start the app using docker
    cmd = f"""
    docker build . -t {IMAGE_NAME} && \\
    docker run -e ELASTICSEARCH_URL={ES_URL} \\
               -e WORKSPACE_URL={WS_URL} \\
               -e USER_PROFILE_URL={USER_PROFILE_URL} \\
               -e WORKERS=2 \\
               -e INDEX_PREFIX={INDEX_PREFIX} \\
               -e INDEX_PREFIX_DELIMITER=. \\
               -e DEVELOPMENT=1 \\
               -p 5000:5000 \\
               --network host \\
               {IMAGE_NAME}
    """
    print(f'Running command:\n{cmd}')
    subprocess.Popen(cmd, shell=True)
