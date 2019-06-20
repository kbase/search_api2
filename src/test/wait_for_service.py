"""
Block until the API is running.
"""
import requests
import time


service_healthy = False
timeout = 60
start_time = int(time.time())
elapsed = 0

while not service_healthy:
    print("Waiting for API to be healthy..")
    try:
        requests.get('http://web:5000/').raise_for_status()
        service_healthy = True
    except Exception:
        print("Unable to connect to API, waiting..")
        elapsed = int(time.time()) - start_time
        if elapsed > timeout:
            raise RuntimeError('Service did not start in {timeout}s. Check the app logs.')
        time.sleep(5)

print('Service is up!')
