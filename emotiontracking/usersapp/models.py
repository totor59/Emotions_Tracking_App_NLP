from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    date_of_registration = models.DateField(default=timezone.now)
    is_patient = models.BooleanField(default=False)


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Patient(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField()
    patient_left = models.BooleanField(default=False)
    date_of_registration = models.DateField(default=timezone.now)
    followed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, to_field='username')
    
    def __str__(self):
        return self.username
