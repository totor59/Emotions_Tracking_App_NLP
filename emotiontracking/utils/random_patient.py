import os
import sys
import django
import random
from faker import Faker
from django.contrib.auth.hashers import make_password
from fake_date import generate_fake_date
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()
from usersapp.models import Patient, CustomUser


def create_random_patient(num_patients):
    faker = Faker()

    for _ in range(num_patients):
        first_name = faker.first_name()
        last_name = faker.last_name()
        username = first_name[0].lower() + last_name.lower() + str(random.randint(10, 99))
        plain_password = username 
        email = f"{username}@example.com"
        date_of_registration = generate_fake_date()
        patient_left = random.choice([True, False])

        followed_by = random.choice(CustomUser.objects.filter(is_patient=False))

        user = CustomUser.objects.create_user(username=username, password=plain_password, email=email, 
                                              first_name = first_name, last_name = last_name, is_patient = True, 
                                              date_of_registration = date_of_registration)
        
        patient = Patient.objects.create(
            patient_id = user, 
            followed_by=followed_by,
            patient_left=patient_left
        )

create_random_patient(20)
