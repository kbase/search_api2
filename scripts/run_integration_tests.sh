#!/bin/sh

cleanup () {
  echo "Stopping container.."
  docker stop $(docker ps -aq)
}

cleanup
trap cleanup EXIT

PYTHONPATH=. pytest -vv -s tests/integration
