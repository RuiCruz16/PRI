# Run the following command `inside` the folder `Milestone2/example_solr`

```
docker run -p 8983:8983 --name meic_solr -v ${PWD}:/data -d solr:9 solr-precreate courses
```
