
# Emotions Tracking Application

## Objectifs 

Ce site est à destination de psychologues et leurs patients.  
Les psychologues peuvent :
- avoir accès à un espace de connexion particulier pour y visualiser la répartition des émotions de leurs patients actifs sur une certaine période de temps.
- visualiser la répartition des émotions d’un de leur patients en recherchant par son nom et prénom.
- rechercher tous les textes contenant une certaines expressions.
- créer un nouveau patient avec un mot de passe par défaut, un nom et un prénom.

Les patients peuvent :
- accéder à un espace privé de connexion.
- créer un nouveau texte.

Les textes écrits par les patients soient automatiquement évalués par un modèle hugging face déployé sur le hub.
Les informations sur les patients et psychologues doivent être enregistrées dans une base postgres.  
Les textes et les évaluations dans une base elastic search.   

## Installation

1. Créer les fichiers .env avec les informations suivantes : 
```
POSTGRES_DB = emotion_db
POSTGRES_USER = main_user
POSTGRES_PASSWORD = pwd
POSTGRES_NAME = emotion_db
DB_HOST = db

SECRET_KEY = secret
DEBUG = True

ELASTICSEARCH_HOST = elasticsearch
ELASTICSEARCH_PORT = 9200

HF_TOKEN = *** your hf token ***
```

2. `docker compose up`  pour démarrer les conteneurs définie dans le fichier *docker-compose.yml*

3. On a maintenant accès à :
- l'application Django : http://localhost:8000/
- la bdd postgresql (avec adminer) : http://localhost:8080/
- la bdd ElasticSearch : http://localhost:9200/

4. Vous pouvez créer vos propres utilisateurs ou vous servir de ceux par défault dont le mot de passe est le username que vous retrouvez dans la bdd postgre 


## Requirements

Vous devez avoir un docker daemon actif


## Crédits
Le projet utilise pour base le répertoire de @MyriamLbhn du même nom