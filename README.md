# Search API

This is a small HTTP interface around KBase's elasticsearch indexes.

## API

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
      "from": 20
    }
  }),
  headers={'Authorization': token}
)
```

#### `show_indexes`

Show the names of all indexes, and show what aliases stand for what indexes.

See [method_schemas.yaml](./src/server/method_schemas.yaml) for JSON Schemas of the request parameters and results.

#### `check_if_doc_exists`

Check for the existence of a doc in some index.

See [method_schemas.yaml](./src/server/method_schemas.yaml) for JSON Schemas of the request parameters and results.

#### Error codes

In a JSON RPC error response, you will find the following error codes:

* `-32000` - Internal server error
* `-32601` - Invalid method
* `-32602` - Invalid request params
* `-32700` - JSON parsing error

### <url>/legacy

A JSON RPC 1.1 API that mimics the legacy Java server, [found here](https://github.com/kbase/KBaseSearchEngin://github.com/kbase/KBaseSearchEngine)

## Development

Start the server:

```sh
docker-compose up
```

Run the tests:

```sh
make test
```

### Deploying to Dockerhub

Increment the docker image tag semver found in `scripts/local-deploy.sh` and run `sh scripts/local-deploy.sh`
