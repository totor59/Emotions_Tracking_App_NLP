import os
import psycopg2
import csv
import sys
import random
from elasticsearch_dsl import connections, Document, Text, Date, Keyword, Integer
from django.utils import timezone
from faker import Faker
from datetime import timedelta

import django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()
from usersapp.models import CustomUser

# Change these settings to match your Elasticsearch service
ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST')
ELASTICSEARCH_PORT = os.environ.get('ELASTICSEARCH_PORT')
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

def populate_index():
    user_id_list = list(CustomUser.objects.values_list('id', flat=True))
    with open('./src/data/Emotion_final.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
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

        


def create_index_and_populate_if_not_exists():
    connections.create_connection(hosts='elasticsearch:9200')  #f'{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}')

    try:
        connections.indices.get(index=INDEX_NAME)
        print("sample texts already created")
    except :
        populate_index()
        print("sample text created")

        

if __name__ == '__main__':
    create_index_and_populate_if_not_exists()