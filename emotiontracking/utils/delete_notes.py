import requests

def delete_documents(index):
    url = f'http://192.168.1.31:9200/{index}/_delete_by_query'
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