import os
import sys
import django

# Ajoutez le chemin du répertoire racine de votre projet Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()

# Importez les modèles après avoir configuré Django
from usersapp.models import Patient, CustomUser
import random
from faker import Faker
from django.contrib.auth.hashers import make_password
from fake_date import generate_fake_date

def create_random_patient():
    faker = Faker()

    num_patients = 20 

    for _ in range(num_patients):
        # Générer les données aléatoires pour chaque patient
        first_name = faker.first_name()
        last_name = faker.last_name()
        username = first_name[0].lower() + last_name.lower() + str(random.randint(100, 999))
        plain_password = username + str(random.randint(10, 99))
        password = make_password(plain_password)
        email = f"{username}@example.com"
        date_of_registration = generate_fake_date()
        patient_left = random.choice([True, False])
        
        # Sélectionner un utilisateur aléatoire qui a is_patient = False
        followed_by = random.choice(CustomUser.objects.filter(is_patient=False))

        # Créer l'objet User associé
        user = CustomUser.objects.create_user(username=username, password=plain_password, email=email, first_name = first_name, last_name = last_name, is_patient = True, date_of_registration = date_of_registration)
        
        # Créer l'objet Patient et l'associer au User
        patient = Patient.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            email=email,
            followed_by=followed_by,
            date_of_registration=date_of_registration,
            patient_left=patient_left
        )

create_random_patient()
