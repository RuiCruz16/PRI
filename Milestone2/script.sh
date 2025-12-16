#!/bin/bash

# This script expects a container started with the following command:
# docker run -p 8984:8983 --name pri_proj -v ${PWD}:/data -d solr:9 solr-precreate diseases

# If having problems with collection just delete it and recreate:
# docker exec -it pri_proj solr delete -c diseases
# docker exec -it pri_proj solr create -c diseases

# Schema definition via API (change to improved_schema.json if you want the new/refined schema)
curl -X POST -H 'Content-type:application/json' \
    --data-binary "@./improved_schema.json" \
    http://localhost:8984/solr/diseases/schema

# Populate collection using mapped path inside container
# The -c flag specifies the collection name
# CSV files are automatically detected and processed
docker exec -it pri_proj solr post -c diseases /data/diseases_dataset.csv
