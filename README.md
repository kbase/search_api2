# Search API

This is a small HTTP interface around KBase's elasticsearch indexes.

## API

### Documents and indexes

The [search configuration file](https://github.com/kbase/index_runner_spec/blob/master/config.yaml) details all of the indexes and document types found in the KBase Elasticsearch database.

* `ws_type_to_indexes` shows which KBase workspace types (without versions) map to which unversioned index names
* `ws_subobjects` is a list of indexes that represent KBase "subobjects", such as genome features, that don't have their own dedicated type in the workspace, but do have a dedicated index in Elasticsearch.
* `global_mappings` are Elasticsearch type definitions that are reused in many of the indexes below.
* `latest_versions` map the unversioned index names to the versioned index names that represent the latest type mapping version.
* `aliases` is a list of Elasticsearch index aliases to a list of index names. These are all searchable as index names.
* `mappings` gives the type definitions for every specific index in the Elasticsearch database. Use these type definitions to find out what kind of data you will get back in the search results.

### <url>/rpc

Uses JSON RPC 2.0 format, so all requests should:

* be a POST request
* have a JSON object in the request body
* have a "method" property (string)
* have a "params" property (object)

#### `search_objects`

Generic search endpoint. Refer to the [Elasticsearch 7 Request Body Search](https://www.elastic.co/guide/en/elasticsearch/reference/7.x/search-request-body.html) documentation, as well as the pages on [aggregations](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html), [sorting](https://www.elastic.co/guide/en/elasticsearch/reference/7.5/search-request-body.html#request-body-search-sort), and [highlighting](https://www.elastic.co/guide/en/elasticsearch/reference/7.5/search-request-body.html#request-body-search-highlighting).

See [method_schemas.yaml](./src/server/method_schemas.yaml) for JSON Schemas of the request parameters and results.

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

See [method_schemas.yaml](./src/server/method_schemas.yaml) for JSON Schemas of the request parameters and results.

#### Error codes

In a JSON RPC error response, you will find the following error codes:

* `-32000` - Internal server error
* `-32601` - Invalid method
* `-32602` - Invalid request params
* `-32700` - JSON parsing error

More useful details of the error will be found in the `message` and `data` properties in the response.

### <url>/legacy

A JSON RPC 1.1 API that mimics the legacy Java server, [found here](https://github.com/kbase/KBaseSearchEngin://github.com/kbase/KBaseSearchEngine). Refer to the KBaseSearchEngine.spec KIDL file for the API.

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

### Deploying to Dockerhub

Increment the docker image tag semver found in `scripts/local-deploy.sh` and run `sh scripts/local-deploy.sh`
