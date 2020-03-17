# Search 2 Setup for Local Development

This document describes a workflow for local development of the searchapi alongside the search indexer, specs, and kbase-ui.

## Setup repos and dependencies

### Create working directory

It is best if all of these repos are cloned in the same working directory. It is required for working on kbase-ui + a plugin.

### clone search api

```text
git clone https://github.com/kbase/search_api_deluxe
```

### clone search index runner

```text
git clone https://github.com/kbase/index_runner_deluxe
```

### get elastic search

We use a seaprate ES instance because we want to ensure it has a persistent set of indexes. The ES container will store it's data files in a Docker volume.

> TODO: the config for this should do a manual volume mount to a local dir.

see 

https://www.elastic.co/guide/en/elasticsearch/reference/7.5/docker.html 

or 

```text
docker pull elasticsearch:7.6.0
```

### set up docker network

create a local private docker network for things to talk across

```text
docker network create kbase-dev
```

> This is the same network used by kbase-ui, which provides proxying to local services.

### start elastic search


```text
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" --net kbase-dev -v esdata:/usr/share/elasticsearch/data elasticsearch:7.6.0
```

or

Once it is started the first time, you can use Docker Desktop to stop and start it.

## Index some data

[ this section still being written ]

### start kafka

```text
cd local-dev
docker-compose up
```

setup for the indexer is via env variables. there are many, but the required ones for us are:

- `SKIP_RELENG=1`
- `ALLOW_INDICES=narrative`
- `ELASTICSEARCH_HOST=elasticsearch`
- `ELASTICSEARCH_PORT=9200`
- `KAFKA_SERVER=kafka`
- `KAFKA_CLIENTGROUP=search_indexer`
- `KBASE_ENDPOINT=https://ci.kbase.us/services`
- ``GLOBAL_CONFIG_URL=file:$(cd `pwd`/../index_runner_spec && pwd)``
- `WORKSPACE_TOKEN=`YOUR CI LOGIN TOKEN
- `WS_ADMIN=``yes` or `no` (or 1 or 0, or true or false, or t or f, or any combination thereof)
- `WS_USER=`USERNAME ASSOCIATED WITH WS TOKEN IF `WS_ADMIN` is 0

> TODO: perhaps replace WS_ADMIN/WS_USER with DEV_USERNAME which would both set WS_ADMIN to false (by default true), and set the username associated with the token.
> 
> On the other hand, if we could take the token and call the WS to determine if it has admin privs, and call auth to get the username, we would not have to manually configure.

## Tasks

### With unit tests

[ to write ]

### With integration tests

[ to write ]

### With data-search ui plugin

[ to write ]



This is all wrapped up in a script `start-local-devstart.sh`

manually build:

```text
docker build --tag indexrunner .
```

set the auth token in the environment:

```text
export WORKSPACE_TOKEN=TOKEN
```

manually invoke:

```text
docker run --rm --net kbase-dev --add-host ci.kbase.us:128.3.56.133 --mount type=bind,source="$(pwd)"/../index_runner_spec,target=/app/config --env SKIP_RELENG=1 --env ALLOW_INDICES=narrative_1 --env ELASTICSEARCH_HOST=elasticsearch --env ELASTICSEARCH_PORT=9200 --env KAFKA_SERVER=kafka --env KAFKA_CLIENTGROUP=search_indexer --env KBASE_ENDPOINT=https://ci.kbase.us/services --env WS_ADMIN=no --env GLOBAL_CONFIG_URL=file://localhost/app/config/confg.yaml --name indexrunner indexrunner:latest
```

manually index:

```text
docker exec indexrunner indexer_admin reindex --overwrite --ref 47458
```

in order to index all of the workspaces for a user, or some subset, you'll need to write a script to automate this, or have a simple shell script with server lines like those above, but with the the workspace id replaced. You can speed this up by using an object ref like `4758/1` rather than a workspace ref.

## References

- https://www.elastic.co/guide/en/elasticsearch/reference/7.5/docker.html

## Issues / TODO

### Separate RE from Search indexing?

it makes the setup and indexing logic more complex

### Earlier exit for evaluating index?

When filtering which indexes are to be utilized, it is only necessary to have the object type info. However, by the time that process is undertaken, the entire object has been fetched, and the associatd indexer run. Pretty inefficient if the index is to be skipped.

### Need a mode to run as developer with non-admin token

in progress

### overwrite should also index for first time

When using the admin tool with an existing index, `--overwrite` must be used; on the other hand, if the index doesn't exist `--overwrite` will prevent the new item from being indexed.

I would think that the normal mode would be create or overwrite, with stricter behavior being an option.

### Indexer error

What should an indexer do if data is non-compliant? E.g. a narrative without correct metadata? I guess throw error...

so i implemented this by the indexer returning an 'error' action with the error message provided. this then is logged in es.

### Indexing after error

requires --overwrite, rather than simple retry.

### Narrative index changes

- add `owner` field
- add `is_temporary`
- add `is_narratorial` or `narrative_type`


```text
/usr/bin/kafka-streams-application-reset --application-id 1 --input-topics=indexeradminevents,worksrpaceevents
```

## NEXT

- need get_permissions_mass to determine if the shared users can be exposed?
- figure out query for determining if a narrative is shared with but not owned by the given user

## Current setup

- elasticsearch
  - container via docker desktop
- kafka/zookeeper: via 
  - `index_runner_deluxe/local-dev/kafka`
  - `docker-compose up`
- index runner via 
  - `index_runner_deluxe/local-dev/run.sh` or `run_narrative.sh`
- run indexer script from 
  - `index_runner_deluxe/local-dev`
  - `ruby index-user-workspaces.rb`
- run api from
  - `search_api_deluxe`
  - `docker-compose -f ./docker-compose.integration-test.yaml up`
- kbase-ui must be running for the proxy and /etc/hosts pointing to local ui

## okay, indexing

set up indexing of all public narratives in ci

ran into a sharding issue

this setting

```text
PUT /*/_settings
```

```json
{
"index" : {
"number_of_replicas":0,
"auto_expand_replicas": false
}
}
```

may fix it temporarily. the problem is too many shards per index (?), and the number of replicas defaults to 1 which doubles this. it is still an issue, but this puts it off a bit.

need to get a grip on tuning ES for dev usage (no replication) as well as deployment (some replication). this is an ES7 new thing.

This worked for a while, then needed another

```text
PUT http://localhost:9200/_cluster/settings
```

```json
{"transient":{"cluster.max_shards_per_node":5000}}
```