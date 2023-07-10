#!/bin/bash

ELASTICSEARCH_HOST="$ELASTICSEARCH_HOST"

curl -X PUT "http://$ELASTICSEARCH_HOST:9200/notes" -H 'Content-Type: application/json' -d '
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
