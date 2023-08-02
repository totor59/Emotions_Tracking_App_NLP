# Views

###home
- l'url renvoie code 200
- (l'url renvoie le bon template)

###register
GET
- l'url renvoie code 200
- le get propose bien le bon formulaire
- patient lef count + patient not left count = patient count.
POST
- si le formulaire est valide, on est redirigé
- si le formulaire est valide on est logué
- si le formulaire n'est pas valide on est redirigé
- si le formulaire n'est pas valide on est pas logué

###Profil
- si on est logué, on y accède (200)
- si on est pas logué, on y accède pas 
- les informations du contexte correspondent aux informations de la personne loguées
- si valide: on est redirigé, ce sont bien les bonnes informations
- si non valide: on reste avec les anciennes infos.

###create_patient
- si on est logué, on y accède (200)
- si on est pas logué, on y accède pas 
- si le formulaire est valide: un user/patient est créé avec les infos du formulaire
- si le formulaire est valide, le psy user a un patient en plus avec les infos du formulaire.
- si invalide:rien n'est créé en bdd

### patient_credentials
- l'url renvoie code 200


### patient_infos
- si on est logué, on y accède (200)
- si on est pas logué, on y accède pas 
- affiche l'ensemble des patients du psy
- que les patients affichés soient ceux du psy qui fait la requete
- si un filtre nom est demandé qu'il fonctionne -> ne marche pas
- (si un filte date est demandé qu'il fonctionne)-> pas testable en l'état
- que l'histogramme reprenne l'ensemble des patients


# Utils

### get_patient_list_info
- Autant de patient que le psy en a
- Que des patient du spy
- que des textes écrits entre les deux dates
- Autant de texte que les patients du psy (occurence)
- Autant d'émotions que d'occurence
- les émotions ne sont que celle de l'app


### get_date_range
- get date range when get
- get date range when post

### generatehistogram (chat gpt)
- verifier que la fonction retourne un string non vide
- vérifier que ce qui ait retourné une fois décodé correspond à un entier non vide
- vérifier qu l'image est un png valide