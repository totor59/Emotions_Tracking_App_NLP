
from elasticsearch import Elasticsearch
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')  # or 'pdf'
import base64
from io import BytesIO
from usersapp.models import Patient
import requests
import time

from django.db.models import Q

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

def get_patient_list_info(filter_name,psy_id,start_date, end_date,es):
    patients = Patient.objects.filter(followed_by_id=psy_id, patient_left=False)
    
    if filter_name != '':
        patients = patients.filter(
            Q(patient_id__first_name__icontains=filter_name) |
            Q(patient_id__last_name__icontains=filter_name)
        )
    
    
    # Créer une liste pour stocker les informations des patients
    emotions = []
    occurrences = []
    patient_infos = []
    
    for patient in patients:
        # Récupérer l'objet CustomUser associé au patient
        custom_user = patient.patient_id
        
        # Ajouter les informations du patient à la liste
        patient_info = {
            'first_name': custom_user.first_name,
            'last_name': custom_user.last_name,
            'username': custom_user.username,
            'date_of_registration': custom_user.date_of_registration,
        }
        patient_infos.append(patient_info)
        
        # Récupérer les émotions du patient à partir d'Elasticsearch
        patient_id = custom_user.id
        response = request_emotion(patient_id, es, start_date, end_date)
        
        emotions, occurrences = generate_emotion_distribution(emotions, occurrences, response)
    
    return patients, patient_infos, emotions, occurrences


def get_date_range(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

    return start_date, end_date

def query_model(payload):
    mapping_dict = {"LABEL_0": 'anger', "LABEL_1": 'fear', "LABEL_2": 'happy', "LABEL_3": 'love', "LABEL_4": 'sadness', "LABEL_5": 'surprise'}
    API_URL = "https://api-inference.huggingface.co/models/Charles-59800/my-awesome-model"
    headers = {"Authorization": f"Bearer {os.environ.get('HF_TOKEN')}"}
    
    
    max_retries=5
    retry_delay=5

    retries = 0

    while retries < max_retries:
        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()[0]
            print(data)
            max_score_label = max(data, key=lambda x: x['score'])['label']
            print(max_score_label)
            return mapping_dict[max_score_label]
        elif response.status_code == 503:
            print("API not ready, retrying...")
            retries += 1
            time.sleep(retry_delay)
        else:
            print(f"Unexpected status code: {response.status_code}. Exiting.")
            break

    print(f"Max retries exceeded. API did not become ready.")
    return None


    
