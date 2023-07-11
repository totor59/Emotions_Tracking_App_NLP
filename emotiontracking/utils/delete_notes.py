import requests
import os

elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')

def delete_documents(index):
    url = f'http://{elasticsearch_host}/{index}/_delete_by_query'
    query = {
        "query": {
            "match_all": {}
        }
    }
    response = requests.post(url, json=query)

    if response.status_code == 200:
        print("Suppression des documents terminée.")
    else:
        print("Erreur lors de la suppression des documents.")

# Utilisation de la fonction
delete_documents('notes')