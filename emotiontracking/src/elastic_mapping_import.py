import os
import psycopg2
import csv
import sys
import random
import time
from elasticsearch_dsl import connections, Document, Text, Date, Keyword, Integer
from elasticsearch import Elasticsearch, TransportError
from django.utils import timezone
from faker import Faker
from datetime import timedelta
import requests
import django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()
from usersapp.models import CustomUser

# Change these settings to match your Elasticsearch service

INDEX_NAME = 'notes'

class NoteDocument(Document):
    text = Text()
    emotion = Keyword()
    date = Date()
    patient_id = Integer()

    class Index:
        name = INDEX_NAME

    def save(self, **kwargs):
        return super(NoteDocument, self).save(**kwargs)

def generate_fake_date_between(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    fake_datetime = start_date + timedelta(days=random_days)
    return fake_datetime

def populate_index(elasticsearch_host_port):
    connections.create_connection(hosts=elasticsearch_host_port)
    user_id_list = list(CustomUser.objects.filter(is_patient=True).values_list('id', flat=True))
    with open('./src/data/Emotion_final.csv', 'r') as file:
        reader = csv.DictReader(file)
        count = 0
        for row in reader:
            if count>=400:
                break
            else:
                # Génération des valeurs Faker pour les champs nom et prenom
                text = row['Text']
                emotion = row['emotion']
                user_id = random.choice(user_id_list)
                user = CustomUser.objects.get(id=user_id)
                date_of_registration = user.date_of_registration

                today = timezone.now().date()
                fake_date = generate_fake_date_between(date_of_registration, today)
                note = NoteDocument(text=text, emotion=emotion, date=fake_date, patient_id=user_id)
                note.save()
                count+=1

def elasticsearch_setting(elasticsearch_url):
    # Disable disk threshold setting
        cluster_settings_url = f"{elasticsearch_url}/_cluster/settings"
        cluster_settings_data = {
            "transient": {
                "cluster.routing.allocation.disk.threshold_enabled": False
            }
        }

        response_cluster = requests.put(
            cluster_settings_url, 
            json=cluster_settings_data, 
            headers={"Content-Type": "application/json"}
        )

        # Set read_only_allow_delete to null for all indices
        all_settings_url = f"{elasticsearch_url}/_all/_settings"
        all_settings_data = {
            "index.blocks.read_only_allow_delete": None
        }

        response_all_indices = requests.put(
            all_settings_url, 
            json=all_settings_data, 
            headers={"Content-Type": "application/json"}
        )

        # Check the responses (optional)
        print("Cluster Settings Response:")
        print(response_cluster.text)
        print("\nAll Indices Settings Response:")
        print(response_all_indices.text)     


def create_index_and_populate_if_not_exists():
    es_host = os.environ.get('ELASTICSEARCH_HOST')
    es_port = os.environ.get('ELASTICSEARCH_PORT')
    elasticsearch_host_port = f'{es_host}:{es_port}'
    elasticsearch_url = "http://" + elasticsearch_host_port

    retries = 60
    retry_delay = 10  # in seconds
    retry_timeout = 3  # in seconds

    while retries > 0:
        try:
            es = Elasticsearch(elasticsearch_host_port)
            print("Connected to Elasticsearch")
            try:
                es.indices.get(index=INDEX_NAME)
                print("Sample texts already created")
            except TransportError as e:
                if e.status_code == 404:
                    elasticsearch_setting(elasticsearch_url)
                    populate_index(elasticsearch_host_port)
                    print("Sample text created")
                else:
                    raise  # If there's another error, raise it to handle it separately if needed.
            break  # If the index exists or is created, exit the loop
        except Exception as e:
            print(e)
            retries -= 1
            if retries == 0:
                print(f"Failed to connect to Elasticsearch after {retries} retries. Exiting.")
                break
            print(f"Failed to connect to Elasticsearch. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

# def create_index_and_populate_if_not_exists():
#     ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST')
#     ELASTICSEARCH_PORT = os.environ.get('ELASTICSEARCH_PORT')
#     elasticsearch_host_port = f'{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}'
#     connections.create_connection(hosts=elasticsearch_host_port)

#     elasticsearch_url = "http://" + elasticsearch_host_port

#     try:
#         connections.indices.get(index=INDEX_NAME)
#         print("sample texts already created")
#     except :
#         elasticsearch_setting(elasticsearch_url)
        
#         populate_index()
#         print("sample text created")

        

if __name__ == '__main__':
    create_index_and_populate_if_not_exists()