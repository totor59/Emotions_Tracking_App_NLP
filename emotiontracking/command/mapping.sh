#!/bin/bash

elasticsearch_host=${ELASTICSEARCH_HOST:-"localhost:9200"}

curl -X PUT "http://${elasticsearch_host}/notes" -H 'Content-Type: application/json' -d '
{
  "mappings": {
    "properties": {
      "text": {"type": "text"},
      "date": {"type": "date" },
      "emotion": {"type": "keyword"},
      "patient_username": {"type": "keyword"}
    }
  }
}'
