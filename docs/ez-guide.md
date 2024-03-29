# An E-Z Guide

This is a set of tasks which worked well for me on macOS.

## Unit Testing

### Host dependencies

You will need to have, at a minimum:

- make
- python 3.7
- docker

### Set up python

Install virtual environment for python:

```sh
python -m venv venv
source  venv/bin/activate
python -m pip install --upgrade pip
```

Install `poetry`:

```sh
pip install poetry
```

Unit tests are run locally, so need to install all python dependencies:

```sh
poetry install
```

### Run Tests

> TODO: should be able to run unit tests in a container, to avoid the need for any host-level installs.

Run the tests!

This will run all the unit tests plus associated code quality evaluations.

```sh
make test
```

or for coverage

```sh
make test-coverage
```

> Note: Ensure that https://ci.kbase.us is accessible from the host machine; some unit tests require this (and should not be unit tests!)

To run tests in a given directory or individual test modules:

```sh
WORKSPACE_URL="http://localhost:5555/ws" PYTHONPATH=. poetry run pytest -vv tests/unit/PATH
```

e.g. to run all the `es_client` tests:

```sh
WORKSPACE_URL="http://localhost:5555/ws" PYTHONPATH=. poetry run pytest -vv tests/unit/es_client
```

## Integration Testing

See [Integration Testing](integration-testing.md)


## Using with kbase-ui

This workflow is very handy for working on both the search api back end and search tool front ends.

```
IP="<IP HERE>" SSHHOST="login1.berkeley.kbase.us" SSHUSER="<KBASE DEV USERNAME>" SSHPASS="<KBASE DEV PWD>" make run-dev-server
```

> TODO: complete this doc!