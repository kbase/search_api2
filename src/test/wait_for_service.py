"""
Block until the API is running.
"""
import requests
import time


service_healthy = False
timeout = 60
start_time = int(time.time())
url = 'http://localhost:5000/'

while not service_healthy:
    print(f"Waiting for Search API ({url}) to be healthy...")
    try:
        requests.get(url).raise_for_status()
        service_healthy = True
    except Exception:
        print(f"Unable to connect to Search API ({url}), waiting...")
        if (int(time.time()) - start_time) > timeout:
            raise RuntimeError('Service did not start in {timeout}s. Check the app logs.')
        time.sleep(5)

print('Service is up!')
