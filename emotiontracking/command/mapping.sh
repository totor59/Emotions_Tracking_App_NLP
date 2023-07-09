#!/bin/bash

curl -X PUT "http://192.168.1.31:9200/notes" -H 'Content-Type: application/json' -d '
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