#!/bin/bash

# RUN THIS SCRIPT IN THE Milestone2/ FOLDER

chmod +x scripts/plot_pr.py
chmod +x scripts/qrels2trec.py
chmod +x scripts/query_solr.py
chmod +x scripts/solr2trec.py

./scripts/query_solr.py \
    --queries queries \
    --uri http://localhost:8984/solr \
    --collection diseases | \
./scripts/solr2trec.py > results_trec.txt

./scripts/qrels2trec.py --qrels qrels > qrels_trec.txt

# If you do not have trec_eval installed, do:
# git clone https://github.com/usnistgov/trec_eval.git trec_eval
# cd trec_eval && make
# cd ..

./trec_eval/trec_eval -q -m all_trec qrels_trec.txt results_trec.txt

./trec_eval/trec_eval -q -m all_trec \
  qrels_trec.txt results_trec.txt | \
./scripts/plot_pr.py

rm qrels_trec.txt
rm results_trec.txt
