# Search API

This is a small HTTP interface around KBase's elasticsearch indexes.

## API

This service has two JSON-RPC 2.0 endpoints:

* `/legacy` - mirrors the old Java JSON-RPC 1.1 methods
* `/rpc` - newer API using the Elasticsearch Query DSL

The JSON-Schemas for the legacy methods can be found in `src/search1_rpc/schemas`

The JSON-Schemas for the newer methods (`/rpc`) can be found in `rpc-schema.yaml`

### Documents and indexes

The [search configuration file](https://github.com/kbase/index_runner_spec/blob/master/config.yaml) details all of the indexes and document types found in the KBase Elasticsearch database.

* `ws_type_to_indexes` shows which KBase workspace types (without versions) map to which unversioned index names
* `ws_subobjects` is a list of indexes that represent KBase "sub objects", such as genome features, that don't have their own dedicated type in the workspace, but do have a dedicated index in Elasticsearch.
* `global_mappings` are Elasticsearch type definitions that are reused in many of the indexes below.
* `latest_versions` map the unversioned index names to the versioned index names that represent the latest type mapping version.
* `aliases` is a list of Elasticsearch index aliases to a list of index names. These are all searchable as index names.
* `mappings` gives the type definitions for every specific index in the Elasticsearch database. Use these type definitions to find out what kind of data you will get back in the search results.

### Custom error codes

* `-32001` - authorization failed
* `-32002` - unknown ES index name
* `-32003` - Elasticsearch response error
* `-32004` - User profile service response error
* `-32005` - Unknown workspace type
* `-32006` - Access group missing
* `-32007` - User profile missing


### `<url>/rpc`

Uses [JSON RPC 2.0 format](https://www.jsonrpc.org/specification).

One exception is handling auth, which should be a KBase token passed in the `Authorization` header.

#### `search_objects`

Generic search endpoint. Refer to the [Elasticsearch 7 Request Body Search](https://www.elastic.co/guide/en/elasticsearch/reference/7.x/search-request-body.html) documentation, as well as the pages on [aggregations](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html), [sorting](https://www.elastic.co/guide/en/elasticsearch/reference/7.5/search-request-body.html#request-body-search-sort), and [highlighting](https://www.elastic.co/guide/en/elasticsearch/reference/7.5/search-request-body.html#request-body-search-highlighting).

_Example request_

```py
requests.post(
  "<url>/rpc",
  data=json.dumps({
    "method": "search_objects",
    "params": {
      "query": {
        "bool": {
          "should": [
            { "match": { "narrative_title": "tutorial" } },
            { "match": { "narrative_title": "narratorial" } },
          ],
        },
      },
      "sort": [
        {"creation_date": {"order": "desc"}},
        "_score"
      ],
      "only_private": true,
      "indexes": ["narrative"],
      "fields": [],
      "size": 20,
      "from": 20,
      "track_total_hits": False,
    }
  }),
  headers={'Authorization': token}
)
```

#### `show_indexes`

Show the names of all indexes, and show what aliases stand for what indexes.

### <url>/legacy

A JSON-RPC 1.1 API that mimics the legacy Java server, [found here](https://github.com/kbase/KBaseSearchEngin://github.com/kbase/KBaseSearchEngine). Refer to the `src/search1_rpc/schemas` file for a reference on the method parameter types.

## Development

Set up the python environment:

1. Install Python 3.7 (we suggest using [pyenv](https://github.com/pyenv/pyenv))
1. Install poetry with `pip install poetry`

Run all tests and linters with:

```sh
make test
```

Run individual tests with:

```sh
poetry run pytest test/xyz
```

Note that if you change index names or docs within the database init script
(`init_elasticsearch.py`), then you will likely need to remove and recreate the
volume for the Elasticsearch service to see the changes. You can do this with `docker-compose down -v`.

### Running the integration tests

Under `tests/integration`, there is a set of integration tests that run against CI (KBase staging server).

These do not run in our CI workflow, but are only run manually/locally.

Please see the [integration testing docs](docs/integration-testing.md) for instructions and further information.
