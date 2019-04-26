# Search API

This is a small HTTP interface around KBase's elasticsearch indexes.

## API

Uses JSON RPC format, so all requests should:
* be a POST request
* have a JSON object in the request body
* have a "method" property (string)
* have a "params" property (object)

### `search_objects`

* method: `search_objects`
* params:
  * `query` elasticsearch query object (refer to [the ES docs](https://www.elastic.co/guide/en/elasticsearch/reference/5.5/search-request-body.html))
  * `source` - optional source filters (refer to [the ES docs](https://www.elastic.co/guide/en/elasticsearch/reference/5.5/search-request-source-filtering.html))
  * `indexes` - array of index names (without any prefix). Case insensitive
  * `only_public` - only show public workspace data
  * `only_private` - only show private workspace data
  * `size` - result length to return for pagination
  * `from` - result offset for pagination

## Development

Start the server:

```sh
docker-compose up
```

Run the tests (with the server running):

```sh
make test
```

### Deploying to Dockerhub

Build the image locally, specifying the image name:

```sh
IMAGE_NAME=kbase/search_api:0.0.2 sh hooks/build
```
