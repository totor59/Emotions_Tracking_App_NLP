from usersapp.models import Patient, CustomUser
from usersapp.forms import PatientRegistrationForm, UserProfileForm, RegistrationForm
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone
import random
import base64
from io import BytesIO
from elasticsearch import Elasticsearch
from transformers import pipeline
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')  # or 'pdf'
import os
elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')


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
            patient.username = username.lower()  # Convertir en minuscules
            plain_password = patient.username + str(random.randint(10, 99))  # Mot de passe sans hachage
            patient.password = make_password(plain_password)
            patient.first_name = form.cleaned_data['first_name']  # Récupérer la valeur de l'e-mail
            patient.last_name = form.cleaned_data['last_name']  # Récupérer la valeur de l'e-mail
            patient.email = form.cleaned_data['email']  # Récupérer la valeur de l'e-mail
            
            # Définir le champ followed_by avec l'instance CustomUser de l'utilisateur connecté
            patient.followed_by = request.user
            
            patient.save()

            # Créer l'objet User associé
            user = CustomUser.objects.create_user(username=patient.username, password=plain_password,
                                                  email=patient.email, first_name = patient.first_name, last_name = patient.last_name, is_patient = True, date_of_registration = patient.date_of_registration)

            # Associer le User au Patient
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

def generate_histogram(emotions, occurrences):
    plt.bar(emotions, occurrences)
    plt.xlabel('Emotion')
    plt.ylabel('Occurrences')
    plt.title('Distribution des émotions du patient')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()

    plt.close()

    return image_base64

@login_required  
def patient_list(request, start_date=None, end_date=None):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
    
    es = Elasticsearch([elasticsearch_host])  # Remplacez par votre configuration Elasticsearch

    filter_name = request.GET.get('filter_name', '')
    
    # Récupérer l'ID du psy connecté
    psy_username = request.user.username
    
    # Filtrer les patients en fonction du psy connecté et patient_left=False
    patients = Patient.objects.filter(followed_by_id=psy_username, patient_left=False)
    
    if filter_name != '':
        patients = patients.filter(Q(first_name__icontains=filter_name) | Q(last_name__icontains=filter_name))
    
    # Générer l'histogramme de la distribution des émotions de tous les patients
    emotions = []
    occurrences = []
    
    for patient in patients:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"patient_username": patient.username}}
                    ],
                    "filter": {
                        "range": {
                            "date": {
                                "gte": start_date if start_date else "1970-01-01",
                                "lte": end_date if end_date else "now"
                            }
                        }
                    }
                }
            }
        }
        response = es.search(index='notes', body=query)
        
        for hit in response['hits']['hits']:
            emotion = hit['_source']['emotion']
            if emotion not in emotions:
                emotions.append(emotion)
                occurrences.append(1)
            else:
                index = emotions.index(emotion)
                occurrences[index] += 1
    
    histogram_image = generate_histogram(emotions, occurrences)
    
    context = {
        'patients': patients,
        'filter_name': filter_name,
        'histogram_image': histogram_image,
    }
    return render(request, 'usersapp/patient_list.html', context)

@login_required 
def patient_texts(request, username):
    # Établir une connexion à Elasticsearch
    es = Elasticsearch([elasticsearch_host])  # Remplacez par votre configuration Elasticsearch

    # Requête Elasticsearch pour récupérer les textes du patient spécifique
    query = {
        "size": 100,
        "query": {
            "term": {
                "patient_username": username
            }
        }
    }

    # Exécuter la requête
    response = es.search(index='notes', body=query)

    # Récupérer les textes des résultats de recherche
    texts = [hit['_source']['text'] for hit in response['hits']['hits']]

    context = {
        'patient_username': username,
        'texts': texts
    }
    return render(request, 'patient_texts.html', context)

@login_required 
def patient_info(request, username, start_date=None, end_date=None):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
    try:
        patient = Patient.objects.get(username=username)
    except Patient.DoesNotExist:
        return render(request, 'error.html', {'message': 'Patient not found'})

    es = Elasticsearch([elasticsearch_host])  # Replace with your Elasticsearch configuration

    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"patient_username": patient.username}}
                ],
                "filter": {
                    "range": {
                        "date": {
                            "gte": start_date if start_date else "1970-01-01",
                            "lte": end_date if end_date else "now"
                        }
                    }
                }
            }
        }
    }
    response = es.search(index='notes', body=query)

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

        emotion = hit['_source']['emotion']
        if emotion not in emotions:
            emotions.append(emotion)
            occurrences.append(1)
        else:
            index = emotions.index(emotion)
            occurrences[index] += 1

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



from django.shortcuts import render, redirect
from .forms import TextForm
from elasticsearch import Elasticsearch

# Établir une connexion à Elasticsearch
elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')
es = Elasticsearch(hosts=[elasticsearch_host])

classifier = pipeline("sentiment-analysis", model="michellejieli/emotion_text_classifier")

@login_required
def create_text(request):
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
    # Établir une connexion à Elasticsearch
    elasticsearch_host = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')
    es = Elasticsearch(hosts=[elasticsearch_host])

    # Récupérer les textes du patient courant depuis Elasticsearch
    user_username = request.user.username
    query = {
        'query': {
            'term': {
                'patient_username': user_username
            }
        }
    }
    result = es.search(index='notes', body=query)

    # Extraire les textes et leurs dates de la réponse Elasticsearch
    texts = []
    for hit in result['hits']['hits']:
        text = hit['_source']['text']
        date = hit['_source']['date']
        texts.append({'text': text, 'date': date})

    context = {
        'texts': texts,
    }

    return render(request, 'my_text_list.html', context)
