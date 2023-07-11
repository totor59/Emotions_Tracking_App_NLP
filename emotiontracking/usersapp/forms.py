from django import forms
from .models import CustomUser, Patient

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'last_name', 'first_name', 'email', 'password', 'is_patient']
        widgets = {
            'password': forms.PasswordInput(),
        }
        
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email']

class PatientRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    email = forms.EmailField(label='E-mail')
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']

from django import forms

class TextForm(forms.Form):
    text = forms.CharField(label='Texte', widget=forms.Textarea)
