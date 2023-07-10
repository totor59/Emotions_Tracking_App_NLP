import os
import sys
import django
from transformers import pipeline

classifier = pipeline("sentiment-analysis", model="michellejieli/emotion_text_classifier")

# Ajoutez le chemin du répertoire racine de votre projet Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()
from usersapp.models import CustomUser

import csv
from django.utils import timezone
import random
from elasticsearch_dsl import connections, Document, Text, Date, Keyword
import pickle
from fake_date import generate_fake_date_between
import psycopg2


# Établir une connexion à Elasticsearch
elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')
connections.create_connection(hosts=[elasticsearch_host])

# # Charger le pipeline pré-entraîné
# with open('model/nlp-pipeline-linearsvc.pkl', 'rb') as f:
#     pipeline = pickle.load(f)

# Définir le document Elasticsearch pour les notes
class NoteDocument(Document):
    text = Text()
    emotion = Keyword()
    date = Date()
    patient_username = Keyword()

    class Index:
        name = 'notes'

    def save(self, **kwargs):
        return super(NoteDocument, self).save(**kwargs)


def get_user():
    # Connexion à la base de données PostgreSQL
    conn = psycopg2.connect(
        host='db',
        database='postgres',
        user='postgres',
        password='postgres'
    )
    
    # Création d'un curseur pour exécuter des requêtes
    cursor = conn.cursor()
    
    # Exécution de la requête pour récupérer les IDs des utilisateurs patients
    query = """
        SELECT username FROM usersapp_customuser
        WHERE is_patient = true 
    """
    cursor.execute(query)
    
    # Récupération des usernames des utilisateurs
    user_usernames = [str(row[0]) for row in cursor.fetchall()]
    
    # Fermeture du curseur et de la connexion à la base de données
    cursor.close()
    conn.close()
    
    # Retourne un ID d'utilisateur au hasard parmi ceux récupérés
    if user_usernames:
        return random.choice(user_usernames)
    else:
        return None
    

def populate_index(num_rows):
    with open('data/Emotion_final.csv', 'r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)  # Convertir le lecteur en une liste de lignes

        random_rows = random.sample(rows, num_rows)  # Sélectionner un échantillon aléatoire de lignes

        for row in random_rows:
            text = row['Text']
            emotion = classifier(text)[0]['label']


            # Récupérer la date d'inscription de l'utilisateur
            user_username = get_user()
            user = CustomUser.objects.get(username=user_username)
            date_of_registration = user.date_of_registration

            # Générer une fausse date entre aujourd'hui et la date d'inscription
            today = timezone.now().date()
            fake_date = generate_fake_date_between(date_of_registration, today)

            note = NoteDocument(text=text, emotion=emotion, date=fake_date, patient_username=user_username)
            note.save()


# Appeler la fonction pour remplir l'index avec un nombre spécifié de lignes aléatoires
num_rows_to_populate = 500 # Choisir le nombre de lignes à l'avance
populate_index(num_rows_to_populate)