import requests
import subprocess

from src.utils.wait_for_service import wait_for_service

BASE_URL = "http://localhost:5000"

# Start the services
subprocess.Popen("docker-compose up -d", shell=True)
wait_for_service(BASE_URL, "search2")


def test_rpc_ok():
    """Test a basic status request to /rpc"""
    resp = requests.get(BASE_URL + '/rpc')
    print('resp:', resp.text, resp.status_code)


def test_legacy_ok():
    """Test a basic status request to /legacy"""
    resp = requests.get(BASE_URL + '/legacy')
    print('resp:', resp.text, resp.status_code)
