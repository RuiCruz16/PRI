#!/bin/bash

# This script expects a container started with the following command:
# docker run -p 8984:8983 --name pri_proj -v ${PWD}:/data -d solr:9 solr-precreate diseases

# Populate collection using mapped path inside container
# The -c flag specifies the collection name
# CSV files are automatically detected and processed
docker exec -it pri_proj solr post -c diseases /data/diseases_dataset.csv
