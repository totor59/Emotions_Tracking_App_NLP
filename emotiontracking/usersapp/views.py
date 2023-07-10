from usersapp.models import Patient, CustomUser
from usersapp.forms import PatientRegistrationForm, UserProfileForm, RegistrationForm
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone
import random
from .forms import TextForm
from transformers import pipeline
from .utils import *

def home(request):
	""" Renders the 'home.html' template, the home page of the website.

    Args:
        request (HttpRequest): An object representing the current request.

    Returns:
        HttpResponse: A response object that renders the 'home.html' template.

    """
	return render(request, 'usersapp/home.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'usersapp/register.html', {'form': form})

@login_required
def profil(request):
    user = request.user
    patients_count = Patient.objects.filter(followed_by=user).count()
    patients_left_count = Patient.objects.filter(followed_by=user, patient_left=True).count()
    patients_not_left_count = Patient.objects.filter(followed_by=user, patient_left=False).count()
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profil')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'user': user,
        'form': form,
        'patients_count': patients_count,
        'patients_left_count': patients_left_count,
        'patients_not_left_count': patients_not_left_count,
    }
    return render(request, 'profil.html', context)

@login_required
def create_patient(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            username = form.cleaned_data['first_name'][0] + form.cleaned_data['last_name'] + str(random.randint(100, 999))
            patient.username = username.lower()  
            plain_password = patient.username + str(random.randint(10, 99))  
            patient.password = make_password(plain_password)
            patient.first_name = form.cleaned_data['first_name']  
            patient.last_name = form.cleaned_data['last_name']  
            patient.email = form.cleaned_data['email'] 
            patient.followed_by = request.user
            
            patient.save()

            user = CustomUser.objects.create_user(username=patient.username, password=plain_password,
                                                  email=patient.email, first_name = patient.first_name, 
                                                  last_name = patient.last_name, is_patient = True, 
                                                  date_of_registration = patient.date_of_registration)
            patient.user = user
            patient.save()

            return redirect(reverse('patient_credentials', args=(patient.username, plain_password, patient.email)))
    else:
        form = PatientRegistrationForm()

    return render(request, 'usersapp/create_patient.html', {'form': form})

@login_required
def patient_credentials(request, username, password, email):
    context = {
        'username': username,
        'password': password,
        'email': email,
    }
    return render(request, 'usersapp/patient_credentials.html', context)

@login_required  
def patient_list(request, start_date=None, end_date=None):
    es = connect_to_elasticsearch()

    start_date, end_date = get_date_range(request)
    
    filter_name = request.GET.get('filter_name', '')
    
    psy_username = request.user.username
    
    patients = Patient.objects.filter(followed_by_id=psy_username, patient_left=False)
    
    if filter_name != '':
        patients = patients.filter(Q(first_name__icontains=filter_name) | Q(last_name__icontains=filter_name))
    
    emotions = []
    occurrences = []
    
    for patient in patients:
        response = request_emotion(patient, es, start_date, end_date)
        
        emotions, occurrences = generate_emotion_distribution(emotions, occurrences, response)
    
    histogram_image = generate_histogram(emotions, occurrences)
    
    context = {
        'patients': patients,
        'filter_name': filter_name,
        'histogram_image': histogram_image,
    }
    return render(request, 'usersapp/patient_list.html', context)

@login_required 
def patient_info(request, username, start_date=None, end_date=None):
    es = connect_to_elasticsearch()

    start_date, end_date = get_date_range(request)

    patient = Patient.objects.get(username=username)
    
    response = request_emotion(patient, es, start_date, end_date)

    notes = []
    emotions = []
    occurrences = []
    
    for hit in response['hits']['hits']:
        note = {
            'text': hit['_source']['text'],
            'date': hit['_source']['date'],
            'emotion': hit['_source']['emotion']
        }
        notes.append(note)

    emotions, occurrences = generate_emotion_distribution(emotions, occurrences, response)

    histogram_image = generate_histogram(emotions, occurrences)

    context = {
        'patient': patient,
        'notes': notes,
        'histogram_image': histogram_image,
    }
    return render(request, 'patient_infos.html', context)

@login_required 
def update_patient_left(request, username):
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(username=username)
        except Patient.DoesNotExist:
            return render(request, 'error.html', {'message': 'Patient not found'})
        
        patient.patient_left = request.POST.get('patient_left') == 'True'
        patient.save()
        
    return redirect('patient_list')

@login_required
def create_text(request):
    
    es = connect_to_elasticsearch()
    classifier = pipeline("sentiment-analysis", model="michellejieli/emotion_text_classifier")
    
    if request.method == 'POST':
        form = TextForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            emotion = classifier(text)[0]['label']
            user_username = request.user.username

            # Enregistrer le texte dans la base de données Elasticsearch
            document = {
                'text': text,
                'emotion': emotion,
                'date': timezone.now().date(),
                'patient_username': user_username,
                # Ajoutez d'autres champs si nécessaire
            }
            index_name = 'notes'  # Nom de l'index Elasticsearch
            es.index(index=index_name, body=document)

            return redirect('home')  # Redirige vers la page d'accueil ou une autre page après l'enregistrement du texte
    else:
        form = TextForm()
    return render(request, 'create_text.html', {'form': form})

@login_required
def my_text_list(request):
    es = connect_to_elasticsearch()
    patient =CustomUser.objects.get(username=request.user.username)    
    response = request_emotion(patient, es)
    texts = []
    for hit in response['hits']['hits']:
        text = hit['_source']['text']
        date = hit['_source']['date']
        texts.append({'text': text, 'date': date})

    context = {'texts': texts}

    return render(request, 'my_text_list.html', context)

@login_required
def search_texts(request):
    es = connect_to_elasticsearch()

    if request.method == 'POST':
        query_text = request.POST.get('query_text', '')

        must_filters = []
        if query_text:
            must_filters.append({'match': {'text': query_text}})

        query = {
            "size": 10000,
            'query': {
                'bool': {
                    'must': must_filters
                }
            }
        }
        result = es.search(index='notes', body=query)

        texts = []
        for hit in result['hits']['hits']:
            text = hit['_source']['text']
            date = hit['_source']['date']
            emotion = hit['_source']['emotion']
            patient_username = hit['_source']['patient_username']
            texts.append({'text': text, 'date': date, 'emotion': emotion, 'patient_username': patient_username})

        context = {
            'texts': texts,
            'query_text': query_text,
        }

        return render(request, 'search_texts.html', context)

    return render(request, 'search_texts.html')
