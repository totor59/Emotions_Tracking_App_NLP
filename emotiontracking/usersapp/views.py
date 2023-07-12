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
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = first_name[0] + last_name + str(random.randint(10,99))

            plain_password = username
            user = CustomUser.objects.create_user(
                username=username.lower(),
                password=plain_password,
                email=form.cleaned_data['email'],
                first_name=first_name,
                last_name=last_name,
                is_patient=True,
                date_of_registration=timezone.now()
            )

            patient = Patient.objects.create(
                patient_id=user,
                followed_by=request.user
            )

            return redirect('patient_credentials', username=user.username)
    else:
        form = PatientRegistrationForm()

    return render(request, 'usersapp/create_patient.html', {'form': form})


@login_required
def patient_credentials(request, username):
    context = {
        'username': username,
    }
    return render(request, 'usersapp/patient_credentials.html', context)

@login_required
def patient_list(request, start_date=None, end_date=None):
    es = connect_to_elasticsearch()

    start_date, end_date = get_date_range(request)
    
    filter_name = request.GET.get('filter_name', '')
    
    psy_id = request.user
    
    patients = Patient.objects.filter(followed_by_id=psy_id, patient_left=False)
    
    if filter_name != '':
        patients = patients.filter(
            Q(patient_id__first_name__icontains=filter_name) |
            Q(patient_id__last_name__icontains=filter_name)
        )
    
    emotions = []
    occurrences = []
    
    # Créer une liste pour stocker les informations des patients
    patient_infos = []
    
    for patient in patients:
        # Récupérer l'objet CustomUser associé au patient
        custom_user = patient.patient_id
        
        # Récupérer les informations de l'objet CustomUser
        first_name = custom_user.first_name
        last_name = custom_user.last_name
        username = custom_user.username
        date_of_registration = custom_user.date_of_registration
        
        # Ajouter les informations du patient à la liste
        patient_info = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'date_of_registration': date_of_registration,
        }
        patient_infos.append(patient_info)
        
        # Récupérer les émotions du patient à partir d'Elasticsearch
        patient_id = patient.patient_id_id
        response = request_emotion(patient_id, es, start_date, end_date)
        
        emotions, occurrences = generate_emotion_distribution(emotions, occurrences, response)
        
        
    histogram_image = generate_histogram(emotions, occurrences)
    
    context = {
        'patients': patients,
        'patient_infos': patient_infos,
        'filter_name': filter_name,
        'histogram_image': histogram_image,
    }
    return render(request, 'usersapp/patient_list.html', context)


@login_required 
def patient_info(request, patient_id, start_date=None, end_date=None):
    es = connect_to_elasticsearch()

    start_date, end_date = get_date_range(request)

    patient = Patient.objects.get(id=patient_id)

    custom_user = patient.patient_id
    first_name = custom_user.first_name
    last_name = custom_user.last_name
    email = custom_user.email
    date_of_registration = custom_user.date_of_registration
    
    response = request_emotion(patient_id, es, start_date, end_date)

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
        'custom_user': custom_user,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'date_of_registration': date_of_registration,
        'notes': notes,
        'histogram_image': histogram_image,
    }
    return render(request, 'patient_infos.html', context)

@login_required 
def update_patient_left(request, patient_id):
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(patient_id_id=patient_id)
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
            patient = Patient.objects.get(patient_id=request.user)  
            patient_id = patient.id

            document = {
                'text': text,
                'emotion': emotion,
                'date': timezone.now().date(),
                'patient_id': patient_id,
            }
            index_name = 'notes'  
            es.index(index=index_name, body=document)

            return redirect('home')  
    else:
        form = TextForm()
    return render(request, 'create_text.html', {'form': form})

@login_required
def my_text_list(request):
    es = connect_to_elasticsearch()
    patient = Patient.objects.get(patient_id=request.user)  # Access the Patient object associated with the logged-in user
    patient_id = patient.id
    response = request_emotion(patient_id, es)
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
            patient_id = hit['_source']['patient_id']
            patient = Patient.objects.get(patient_id = request.user)
            username = patient.patient_id.username

            texts.append({'text': text, 'date': date, 'emotion': emotion, 'patient_username': username, 'patient_id': patient_id})

        context = {
            'texts': texts,
            'query_text': query_text,
        }

        return render(request, 'search_texts.html', context)

    return render(request, 'search_texts.html')
