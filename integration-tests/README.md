# Integration Tests

This set of tests is separate from the unit tests, for the time being.

They are `pytest`-based, an instance of the search api running, which in turn must be running run against an elasticsearch instance.

The expectations of the tests are based on specific indexing conditions using data from a kbase environment. At this point, just CI has been set up.

## Using

In one terminal start the searchapi:

```text
docker-compose -f ./docker-compose.integration-test.yaml up
```

In another run the tests

```text
cd integration-tests
```

If you haven't installed pytest yet, then something like this:

```text
virtualenv init .env
source .env/bin/activate
pip install -r requirements.txt
```

```text
TOKEN="YOURTOKEN" URL="http://localhost:5000" pytest
```

## Using with kbase-ui

kbase-ui developers may prefer to stay within that proxying ecosystem. In that case:

- edit /etc/hosts to route ci.kbase.us to localhost
- fire up kbase-ui

```text
make dev-start build-image=t env=ci build=dev services=searchapi2
```

run the integration tests like this:

```text
TOKEN="YOURTOKEN" URL="https://ci.kbase.us/services/searchapi2" pytest
```

## Indexing

Rough and ready notes.

In the search indexer, index some CI workspaces:

```bash
TOKEN=YOURTOKEN ruby index-own-narratives.rb
TOKEN=YOURTOKEN ruby index-narratorials.rb
TOKEN=YOURTOKEN LIMIT=100 ruby index-refseq.rb
TOKEN=YOURTOKEN LIMIT=100 ruby index-mycocosm.rb
```

This should populate the ES database with 158 objects. These objects are the subject of the integration tests.


## TODO

- have the tests run in a docker container. virtualenv, yuck.

