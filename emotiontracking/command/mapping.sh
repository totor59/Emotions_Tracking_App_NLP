#!/bin/bash

curl -X PUT "http://10.16.0.19:9200/notes" -H 'Content-Type: application/json' -d '
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