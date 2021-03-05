# An E-Z Guide

This is a set of tasks which worked well for me on MacOS.

## Unit Testing

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

> TODO: should be able to run unit tests in a container, to avoid the need for any host-level installs.

Run the tests!

This will run all the unit tests plus associated code quality evaluations.

```sh
make test
```

To run tests in a given directory or individual test modules:

```sh
WORKSPACE_URL="http://localhost:5555/ws" PYTHONPATH=. poetry run pytest -vv tests/unit/PATH
```

e.g. to run all the `es_client` tests:

```sh
WORKSPACE_URL="http://localhost:5555/ws" PYTHONPATH=. poetry run pytest -vv tests/unit/es_client
```

## Integration Testing

The integration tests run inside a Docker container. An associated ssh tunnel proxies elastic search requests into KBase. This tunnel is also run in a container. To ease the process of coordinating the startup of these containers, the are scripted in a docker-compose config file.

### Build the images

Although the integration test script will build the images if they are missing, the build can take a few minutes, which may cause the integration test script to time out. It is more reliable to simply build the containers first.

```bash
make build-integration-test-images.sh
```

You can view the files `container.out` and `container.err` to monitor progress building the images.

### Run the integration  tests

First you'll need to set up the required test parameters, which are provided as shell environment variables. How you provide them is up to you, but it is probably easiest (especially for test iteration) to export them:

```bash
export WS_TOKEN="<LOGIN TOKEN FOR TEST USER>"
export IP="<KBASE ES HOST>"
export SHHOST="<KBASE SSH HOST>"
export SSHUSER="<DEV ACCOUNT USERNAME>"
export SSHPASS="<DEV ACCOUNT PASSWORD>"
```

Running the tests is as simple as:

```bash
make integration-Tests
```

The default logging level is "DEBUG" which can emit an annoying level of messages interspersed with test results. I prefer to run the tests like:

```bash
LOGLEVEL=ERROR make integration-tests
```


If all goes well you should see something like:

```bash
(venv) erikpearson@Eriks-MBP-2 search_api2 % LOGLEVEL=ERROR make integration-tests
Running Integraion Tests...
sh scripts/run_integration_tests
+ path=tests/integration
+ export PYTHONPATH=.
+ PYTHONPATH=.
+ poetry run pytest -vv -s tests/integration
=================================================== test session starts ===================================================
platform darwin -- Python 3.7.9, pytest-5.4.3, py-1.9.0, pluggy-0.13.1 -- /Users/erikpearson/work/kbase/sprints/2020Q4/fixes/fix_search_api2_legacy/search_api2/venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/erikpearson/work/kbase/sprints/2020Q4/fixes/fix_search_api2_legacy/search_api2
plugins: cov-2.10.1
collecting ... Logger and level: <Logger search2 (ERROR)>

** To see more or less logging information, adjust the
** log level with the LOGLEVEL environment variable set
** to one of:
**   CRITICAL ERROR WARNING INFO DEBUG NOTSET
** It is currently set to:
**   ERROR

collected 9 items                                                                                                         

tests/integration/test_integration_legacy.py::test_search_example1 PASSED
tests/integration/test_integration_legacy.py::test_search_example2 PASSED
tests/integration/test_integration_legacy.py::test_search_example3 PASSED
tests/integration/test_integration_legacy.py::test_search_example4 PASSED
tests/integration/test_integration_legacy.py::test_search_example5 PASSED
tests/integration/test_integration_legacy.py::test_search_example6 PASSED
tests/integration/test_integration_legacy.py::test_search_case1 PASSED
tests/integration/test_integration_search_workspaces.py::test_narrative_example PASSED
tests/integration/test_integration_search_workspaces.py::test_dashboard_example PASSED

=================================================== 9 passed in 24.27s ====================================================
(venv) erikpearson@Eriks-MBP-2 search_api2 %
``

## Using with kbase-ui

```
IP="<IP HERE>" SSHHOST="login1.berkeley.kbase.us" SSHUSER="<KBASE DEV USERNAME>" SSHPASS="<KBASE DEV PWD>" docker-compose --file tests/integration/docker-compose.yaml up
```