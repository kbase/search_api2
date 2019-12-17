#!/bin/sh
set -e
# show the commands we execute
set -o xtrace
export IMAGE_NAME="kbase/search_api:0.1.1"
sh hooks/build
docker push $IMAGE_NAME
