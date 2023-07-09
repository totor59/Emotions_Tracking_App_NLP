from django.contrib import admin
from .models import  Patient, CustomUser

admin.site.register(CustomUser)
admin.site.register(Patient)
