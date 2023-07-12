#!/bin/bash



curl -X PUT "http://elasticsearch:9200/notes" -H 'Content-Type: application/json' -d '
{
  "mappings": {
    "properties": {
      "text": {"type": "text"},
      "date": {"type": "date" },
      "emotion": {"type": "keyword"},
      "patient_id": {"type": "integer"}
    }
  }
}'
