#!/bin/sh

set -e

export PYTHONPATH=.

poetry run flake8
poetry run mypy --ignore-missing-imports src/**/*.py
poetry run bandit -r src
poetry run pytest -vv test/server
