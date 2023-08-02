from usersapp.models import Patient, CustomUser
from usersapp.forms import PatientRegistrationForm, UserProfileForm, RegistrationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone
import random
from elasticsearch import Elasticsearch
from .forms import TextForm
from .utils import *


def home(request: HttpRequest) -> HttpResponse:
    """Renders the 'home.html' template, the home page of the website.

    Args:
        request (HttpRequest): An object representing the current request.

    Returns:
        HttpResponse: A response object that renders the 'home.html' template.
    """
    return render(request, 'usersapp/home.html')

def register(request: HttpRequest) -> HttpResponse:
    """Renders the 'register.html' template for user registration.

    If the request method is POST, the function processes the submitted form,
    creates a new user account, and redirects to the login page upon successful registration.

    If the request method is GET, it displays an empty registration form.

    Args:
        request (HttpRequest): An object representing the current request.

    Returns:
        HttpResponse: A response object that renders the 'register.html' template with the registration form.
        If the form is successfully submitted, it redirects to the 'login' page.
    """
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
def profil(request: HttpRequest) -> HttpResponse:
    """Renders the 'profil.html' template for the user's profile.

    The function retrieves information related to the user's profile and patients,
    including the total count, the count of patients who left, and the count of patients who haven't left.

    If the request method is POST, the function processes the submitted form
    and updates the user's profile information. It then redirects back to the profile page.

    If the request method is GET, it displays the user's profile information in a form.

    Args:
        request (HttpRequest): An object representing the current request.

    Returns:
        HttpResponse: A response object that renders the 'profil.html' template with the user's profile information.
        If the form is successfully submitted, it redirects back to the 'profil' page.
    """
    user = request.user
    patients_count = Patient.objects.filter(followed_by=user).count()
    patients_left_count = Patient.objects.filter(followed_by=user, patient_left=True).count()
    patients_not_left_count = Patient.objects.filter(followed_by=user, patient_left=False).count()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profil')
    else:
        form = UserProfileForm(instance=user)

    context = {
        'user': user,
        'form': form,
        'patients_count': patients_count,
        'patients_left_count': patients_left_count,
        'patients_not_left_count': patients_not_left_count,
    }
    return render(request, 'profil.html', context)

@login_required
def create_patient(request: HttpRequest) -> HttpResponse:
    """Create a new patient.

    If the request method is POST, the function processes the submitted form,
    creates a new patient account, and redirects to the 'patient_credentials' page.

    If the request method is GET, it displays an empty patient registration form.

    Args:
        request (HttpRequest): An object representing the current request.

    Returns:
        HttpResponse: A response object that renders the 'create_patient.html' template with the patient registration form.
        If the form is successfully submitted, it redirects to the 'patient_credentials' page.
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = first_name[0] + last_name + str(random.randint(10, 99))

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

            Patient.objects.create(
                patient_id=user,
                followed_by=request.user
            )

            return redirect('patient_credentials', username=user.username)
    else:
        form = PatientRegistrationForm()

    return render(request, 'usersapp/create_patient.html', {'form': form})


@login_required
def patient_credentials(request: HttpRequest, username: str) -> HttpResponse:
    """Display patient credentials for the given username.

    Args:
        request (HttpRequest): An object representing the current request.
        username (str): The username of the patient for whom credentials are to be displayed.

    Returns:
        HttpResponse: A response object that renders the 'patient_credentials.html' template
        with the patient's username in the context.
    """
    context = {
        'username': username,
    }
    return render(request, 'usersapp/patient_credentials.html', context)

@login_required
def patient_list(request, start_date=None, end_date=None):
    es = connect_to_elasticsearch()

    filter_name = request.GET.get('filter_name', '')
    psy_id = request.user
    start_date, end_date = get_date_range(request)
    
    patients, patient_infos, emotions, occurrences = get_patient_list_info(filter_name,psy_id,start_date, end_date,es)
        
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

    if request.method == 'POST':
        form = TextForm(request.POST)
        if form.is_valid():
            es_host = os.environ.get('ELASTICSEARCH_HOST')
            es_port = os.environ.get('ELASTICSEARCH_PORT')
            elasticsearch_host_port = f'{es_host}:{es_port}'

            es = Elasticsearch(elasticsearch_host_port)

            text = form.cleaned_data['text']
            emotion = query_model(text)
            patient = Patient.objects.get(patient_id=request.user)  

            document = {
                'text': text,
                'emotion': emotion,
                'date': timezone.now().date(),
                'patient_id': patient.id,
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
            patient_user = CustomUser.objects.get(id = patient_id)
            patient = Patient.objects.get(patient_id = patient_user)
            username = patient.patient_id.first_name + ' ' + patient.patient_id.last_name

            texts.append({'text': text, 'date': date, 'emotion': emotion, 'patient_username': username, 'patient_id': patient_id})

        context = {
            'texts': texts,
            'query_text': query_text,
        }

        return render(request, 'search_texts.html', context)

    return render(request, 'search_texts.html')