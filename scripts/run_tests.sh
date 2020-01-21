#!/bin/sh

set -e

export PYTHONPATH=/app

mypy --ignore-missing-imports src
bandit -r src
sh scripts/start_server.sh &
python src/test/wait_for_service.py &&
python -m unittest discover src/test/
