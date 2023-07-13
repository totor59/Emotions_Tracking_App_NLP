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


from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(), label='Old Password')
    new_password1 = forms.CharField(widget=forms.PasswordInput(), label='New Password')
    new_password2 = forms.CharField(widget=forms.PasswordInput(), label='Confirm New Password')

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.request.user.check_password(old_password):
            raise forms.ValidationError('Old password is incorrect')
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2

    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.request.user.set_password(password)
        if commit:
            self.request.user.save()
        return self.request.user
