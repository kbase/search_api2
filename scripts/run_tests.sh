#!/bin/sh

set -e

export PYTHONPATH=/app

flake8 src test
mypy --ignore-missing-imports src
bandit -r src
sh scripts/start_server.sh &
python test/wait_for_service.py &&
python -m unittest discover test/
