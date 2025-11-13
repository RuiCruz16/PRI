#!/bin/bash

# This script expects a container started with the following command:
# docker run -p 8984:8983 --name pri_proj -v ${PWD}:/data -d solr:9 solr-precreate diseases

# If having problems with collection just delete it and recreate:
# docker exec -it pri_proj solr delete -c diseases
# docker exec -it pri_proj solr create -c diseases

# Schema definition via API
curl -X POST -H 'Content-type:application/json' \
    --data-binary "@./schema.json" \
    http://localhost:8984/solr/diseases/schema

# Populate collection using mapped path inside container
# The -c flag specifies the collection name
# CSV files are automatically detected and processed
docker exec -it pri_proj solr post -c diseases /data/diseases_dataset.csv

<< queries
# Neurological Diseases (Brain/Nervous System)
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "brain^5 neurological^4 neural^4 nervous^3 cognitive^3 dementia^3 seizure*^3 stroke^2 paralysis^2",
  "params": {
    "defType": "edismax",
    "qf": "disease_name^4 symptoms_and_causes^3 overview^2",
    "mm": "2"
  },
  "fields": "*,score",
  "limit": 10
}'

# Respiratory Diseases (Lung/Breathing Focus)
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "lung*^5 respiratory^4 breathing^4 pulmonary^3 asthma^3 pneumonia^3 bronch*^2 \"shortness of breath\"~3^4",
  "params": {
    "defType": "edismax",
    "qf": "symptoms_and_causes^4 disease_name^3 overview^2",
    "mm": "2"
  },
  "fields": "*,score",
  "limit": 10
}'

# Digestive/Gastrointestinal Diseases
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "digestive^5 gastrointestinal^4 stomach^4 intestin*^4 liver^3 colon^3 bowel^3 diarrhea^2 nausea^2",
  "params": {
    "defType": "edismax",
    "qf": "disease_name^4 symptoms_and_causes^3 overview^2",
    "mm": "2"
  },
  "fields": "*,score",
  "limit": 10
}'

# Mental Health/Psychological Conditions
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "mental^5 psychological^4 psychiatric^4 depression^4 anxiety^3 mood^3 emotional^2 \"mental health\"~2^5 -physical",
  "params": {
    "defType": "edismax",
    "qf": "overview^4 symptoms_and_causes^3 living_with^2",
    "mm": "2"
  },
  "fields": "*,score",
  "limit": 10
}'

# Metabolic/Endocrine Diseases
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "metabolic^5 endocrine^4 hormone*^4 thyroid^3 gland*^3 insulin^3 glucose^2 metabolism^2",
  "params": {
    "defType": "edismax",
    "qf": "overview^4 symptoms_and_causes^3 disease_name^2",
    "mm": "2"
  },
  "fields": "*,score",
  "limit": 10
}'

# Cancer/Oncological Diseases
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "cancer^5 tumor*^4 malignant^4 oncolog*^3 carcinoma^3 metasta*^3 chemotherapy^2 radiation^2",
  "params": {
    "defType": "edismax",
    "qf": "disease_name^4 overview^3 management_and_treatment^3 outlook_prognosis^2",
    "mm": "2"
  },
  "fields": "*,score",
  "limit": 10
}'

# Most mortal diseases
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "(death* OR fatal* OR mortal* OR \"high mortality\"~2 OR \"death rate\"~2 OR lethal OR deadly OR terminal OR \"poor prognosis\"~2 OR \"low survival\"~2 OR incurable) OR (\"heart disease\"~2 OR \"ischemic heart\"~2 OR cancer OR stroke OR \"respiratory disease\"~2 OR alzheimer* OR diabetes OR \"kidney disease\"~2 OR tuberculosis OR sepsis OR \"organ failure\"~2)",
  "params": {
    "defType": "edismax",
    "qf": "outlook_prognosis^5 overview^3 disease_name^2 symptoms_and_causes^1.5",
    "mm": "3"
  },
  "fields": "*,score",
  "limit": 20,
  "sort": "score desc"
}'

# Diseases that are treatable with non-pharmaceutical interventions, affect the elderly, and have significant impact on daily living
curl http://localhost:8984/solr/diseases/query -d '{
  "query": "(elderly^4 aging^3 seniors^3 geriatric^3 \"older adults\"~3^3 \"age-related\"^3 \"over 65\"^2 \"retirement age\"^2) AND (chronic^5 persistent^4 long-term^4 \"daily living\"~3^3 \"quality of life\"^3 disability^2 \"functional impairment\"^2) AND (exercise^4 diet^4 lifestyle^3 \"physical therapy\"^3 \"non-pharmaceutical\"^3 \"self-management\"^2 counseling^2) -rare -acute -\"single episode\"~2 -\"childhood onset\"~3",
  "params": {
    "defType": "edismax",
    "qf": "overview^3 symptoms_and_causes^2 management_and_treatment^4 living_with^3 prevention^2 outlook_prognosis^2",
    "mm": "4"
  },
  "fields": "*,score",
  "limit": 15,
  "sort": "score desc"
}'
queries