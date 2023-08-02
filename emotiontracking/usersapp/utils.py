
from elasticsearch import Elasticsearch
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')  # or 'pdf'
import base64
from io import BytesIO
from usersapp.models import Patient
import requests

def connect_to_elasticsearch():
    es = Elasticsearch('elasticsearch:9200')
    return es

def generate_histogram(emotions, occurrences):
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#7C4DFF']
    plt.bar(emotions, occurrences, color=colors)
    plt.xlabel('Emotion')
    plt.ylabel('Occurrences')
    plt.title('Emotion distribution')
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    return image_base64


def request_emotion(patient_id, es, start_date=None, end_date=None):
    if start_date is None:
        start_date = "1970-01-01" 
    if end_date is None:
        end_date = "now" 
    query = {
        "size":500,
        "query": {
            "bool": {
                "must": [
                    {"term": {"patient_id": patient_id}}
                ],
                "filter": {
                    "range": {
                        "date": {
                            "gte": start_date if start_date else "1970-01-01",
                            "lte": end_date if end_date else "now"
                        }
                    }
                }
            }
        }
    }
    response = es.search(index='notes', body=query)

    return response

def generate_emotion_distribution(emotions, occurrences, response):
    for hit in response['hits']['hits']:
            emotion = hit['_source']['emotion']
            if emotion not in emotions:
                emotions.append(emotion)
                occurrences.append(1)
            else:
                index = emotions.index(emotion)
                occurrences[index] += 1
    return(emotions, occurrences)

def get_date_range(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

    return start_date, end_date

def query_model(payload):
    mapping_dict = {"Label_0": 'anger', "Label_1": 'fear', "Label_2": 'happy', "Label_3": 'love', "Label_4": 'sadness', "Label_5": 'surprise'}
    API_URL = "https://api-inference.huggingface.co/models/Charles-59800/my-awesome-model"
    headers = {"Authorization": f"Bearer {os.environ.get('HF_TOKEN')}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return mapping_dict[response.json()[0]['label']]
