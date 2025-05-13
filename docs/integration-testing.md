# Integration Testing

The integration tests run inside a Docker container. An associated ssh tunnel proxies elastic search requests into KBase. This tunnel is also run in a container. To ease the process of coordinating the startup of these containers, the are scripted in a docker-compose config file.

### Build the images

Although the integration test script will build the images if they are missing, the build can take a few minutes, which may cause the integration test script to time out. It is more reliable to simply build the containers first.

```bash
make build-dev-images
```

You can view the files `container.out` and `container.err` to monitor progress building the images.

### Run the integration  tests

First you'll need to set up the required test parameters, which are provided as shell environment variables. How you provide them is up to you, but it is probably easiest (especially for test iteration) to export them:

```bash
export WS_TOKEN="<LOGIN TOKEN FOR TEST USER>"
export IP="<KBASE ES HOST>"
export SSHHOST="<KBASE SSH HOST>"
export SSHUSER="<DEV ACCOUNT USERNAME>"
export SSHPASS="<DEV ACCOUNT PASSWORD>"
```

> Note: For now, the "test user" is `kbaseuitest`. Ask a kbase-ui dev in the #ui channel for the password to obtain the `WS_TOKEN`.

> TODO: We should establish a `searchtest` user, use it to create some narratives with data for indexing, and use that account for integration testing. 


Running the tests is as simple as:

```bash
make integration-tests
```

The default logging level is "DEBUG" which can emit an annoying level of messages interspersed with test results. I prefer to run the tests like:

```bash
LOGLEVEL=ERROR make integration-tests
```

If all goes well you should see something like:

```bash
➤➤ search_api2 (dev-add_workflows) $ make integration-tests
Running Integration Tests...
sh scripts/run_integration_tests
+ path=tests/integration
+ export PYTHONPATH=.
+ PYTHONPATH=.
+ poetry run pytest -v tests/integration
=========================================================================== test session starts ===========================================================================
platform darwin -- Python 3.9.19, pytest-6.2.2, py-1.10.0, pluggy-0.13.1 -- /Users/sijiex/anaconda3/envs/index/bin/python
cachedir: .pytest_cache
rootdir: /Users/sijiex/Documents/LBNL/security/search_api2
plugins: anyio-4.9.0, cov-2.11.1
collected 15 items

tests/integration/test_integration_search_workspaces.py::test_narrative_example PASSED                                                                              [  6%]
tests/integration/test_integration_search_workspaces.py::test_dashboard_example PASSED                                                                              [ 13%]
tests/integration/test_legacy_search_objects.py::test_search_objects_public PASSED                                                                                  [ 20%]
tests/integration/test_legacy_search_objects.py::test_search_example3 PASSED                                                                                        [ 26%]
tests/integration/test_legacy_search_objects.py::test_search_objects_private PASSED                                                                                 [ 33%]
tests/integration/test_legacy_search_objects.py::test_search_objects_multiple_terms_narrow PASSED                                                                   [ 40%]
tests/integration/test_legacy_search_objects.py::test_search_objects_ PASSED                                                                                        [ 46%]
tests/integration/test_legacy_search_objects.py::test_search_case_01_no_auth PASSED                                                                                 [ 53%]
tests/integration/test_legacy_search_objects.py::test_search_objects_many_results PASSED                                                                            [ 60%]
tests/integration/test_legacy_search_objects.py::test_search_objects_private_and_public_counts PASSED                                                               [ 66%]
tests/integration/test_legacy_search_objects.py::test_search_objects_private_counts PASSED                                                                          [ 73%]
tests/integration/test_legacy_search_objects.py::test_search_objects_public_counts PASSED                                                                           [ 80%]
tests/integration/test_legacy_search_objects.py::test_search_objects_neither_private_nor_public PASSED                                                              [ 86%]
tests/integration/test_legacy_search_objects.py::test_search_objects_public_vs_private PASSED                                                                       [ 93%]
tests/integration/test_legacy_search_types.py::test_search_types PASSED                                                                                             [100%]

====================================================================== 15 passed in 87.24s (0:01:27) ======================================================================
```
