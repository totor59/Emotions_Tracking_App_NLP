
# Emotions Tracking Application

## Objectifs 

## Installation

1. Créer les fichiers .env avec les informations suivantes : 
```
POSTGRES_DB=au_choix
POSTGRES_USER=nom_utilisateur_au_choix
POSTGRES_PASSWORD=mdp_au_choix
POSTGRES_NAME=nom_bdd_au_choix
DB_HOST=db

SECRET_KEY = 'votre_secret_key_django'
DEBUG = True

ELASTICSEARCH_HOST=adresse_ip:9200
```

2. `docker compose up`  pour démarrer les conteneurs d'une application multi-conteneurs définie dans un fichier *docker-compose.yml*

3. On a maintenant accès à :
- l'application Django : http://localhost:8000/
- la bdd postgresql (avec adminer) : http://localhost:8080/
- la bdd ElasticSearch : http://localhost:9200/

4. Pour executer ouvrir le shell du conteneur django : `docker compose exec web bash`

5. Depuis ce shell, vous pouvez créer un superuser si vous souhaitez : `python manage.py createsuperuser`

6. Il faut maintenant créer au moins 1 compte en tant que psychologue (depuis le portail admin ou depuis http://localhost:8000/register/)

7. Pour remplir nos bdd, dans le shell du conteneur django : 
- `python utils/random_patient.py`: crée x patients (vous pouvez modifier ce nombre directement dans le fichier python, la variable *num_patient*)
- `python ./command/mapping.sh`pour créer l'index note 
- `python utils/populate_index.py` pour créer x document (vous pouvez modifier ce nombre directement dans le fichier python, la variable *num_row_to_populate*)

8. Vous pouvez maintenant naviguer sur l'application et accéder à toutes ses fonctionnalités.

## Arborescence de fichier