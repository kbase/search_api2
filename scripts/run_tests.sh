#!/bin/sh

set -e

export PYTHONPATH=/app

mypy --ignore-missing-imports src
bandit -r src
python -m unittest discover src/test/
