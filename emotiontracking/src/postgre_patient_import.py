import os
import sys
import django
import random
from faker import Faker
from datetime import datetime,timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emotiontracking.settings')
django.setup()
from usersapp.models import Patient, CustomUser

def generate_fake_date():
    faker = Faker()
    max_date = datetime.now()
    min_date = max_date - timedelta(days=730)  # 2 ans
    return faker.date_between_dates(min_date, max_date)

def create_user(is_patient):
    faker = Faker()
    first_name = faker.first_name()
    last_name = faker.last_name()
    username = first_name[0].lower() + last_name.lower() + str(random.randint(10, 99))
    plain_password = username 
    email = f"{username}@example.com"
    date_of_registration = generate_fake_date()
    user = CustomUser.objects.create_user(username=username, password=plain_password, email=email, 
                                              first_name = first_name, last_name = last_name, is_patient = is_patient, 
                                              date_of_registration = date_of_registration)
    return user

def create_random_psy(num_psy):
    for _ in range(num_psy):
        create_user(is_patient=False)

def create_random_patient(num_patients):
    for _ in range(num_patients):
        user = create_user(is_patient=True)
        
        patient_left = random.choice([True, False])
        followed_by = random.choice(CustomUser.objects.filter(is_patient=False))

        Patient.objects.create(
            patient_id = user, 
            followed_by=followed_by,
            patient_left=patient_left
        )
    print("patients created")

if not Patient.objects.exists():
    create_random_psy(2)
    create_random_patient(30)
else:
    print("patients already created")
