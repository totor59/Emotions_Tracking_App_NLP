from datetime import datetime, timedelta
from faker import Faker
import random
from django.utils import timezone


def generate_fake_date():
    faker = Faker()
    max_date = datetime.now()
    min_date = max_date - timedelta(days=730)  # 2 ans
    return faker.date_between_dates(min_date, max_date)


def generate_fake_date_between(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    fake_datetime = start_date + timedelta(days=random_days)
    return fake_datetime