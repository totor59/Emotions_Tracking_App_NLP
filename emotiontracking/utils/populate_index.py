import os
import sys
import django
from transformers import pipeline
import csv
from django.utils import timezone
import random
from elasticsearch_dsl import connections, Document, Text, Date, Keyword, Integer
from fake_date import generate_fake_date_between
import psycopg2
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()
from usersapp.models import CustomUser


elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')
connections.create_connection(hosts=[elasticsearch_host])

classifier = pipeline("sentiment-analysis", model="michellejieli/emotion_text_classifier")

class NoteDocument(Document):
    text = Text()
    emotion = Keyword()
    date = Date()
    patient_id = Integer()

    class Index:
        name = 'notes'

    def save(self, **kwargs):
        return super(NoteDocument, self).save(**kwargs)


def get_user_id():
    conn = psycopg2.connect(
        host='db',
        database=os.environ.get('POSTGRES_NAME'),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD')
    )
    
    cursor = conn.cursor()
    
    query = """
        SELECT id FROM usersapp_customuser
        WHERE is_patient = true 
    """
    cursor.execute(query)
    
    user_id = [str(row[0]) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    if user_id:
        return random.choice(user_id)
    else:
        return None
    

def populate_index(num_texts):
    with open('data/Emotion_final.csv', 'r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)  

        random_rows = random.sample(rows, num_texts)  
        for row in random_rows:
            text = row['Text']
            emotion = classifier(text)[0]['label']

            user_id = get_user_id()
            user = CustomUser.objects.get(id=user_id)
            date_of_registration = user.date_of_registration

            today = timezone.now().date()
            fake_date = generate_fake_date_between(date_of_registration, today)

            note = NoteDocument(text=text, emotion=emotion, date=fake_date, patient_id=user_id)
            note.save()

populate_index(500)