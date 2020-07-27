#!/bin/sh

cleanup () {
  echo "Stopping container.."
  docker stop $(docker ps -aq)
}

cleanup
trap cleanup EXIT
path=${1:-"tests/integration"}
export PYTHONPATH=.
poetry run pytest -vv -s $path
