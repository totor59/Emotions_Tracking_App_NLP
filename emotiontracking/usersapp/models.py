from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    last_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    date_of_registration = models.DateField(default=timezone.now)
    is_patient = models.BooleanField(default=False)


class Patient(models.Model):
    patient_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    patient_left = models.BooleanField(default=False)
    followed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='patient_followed_by')

    def __str__(self):
        return self.patient_id.username

