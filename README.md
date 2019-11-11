# ProjetNLP_jury
Version définitive du projet NLP

Quatre points importants à revoir

* BDD : utilisation ORM ou non
* Login gestionnaire des formulaires : voir comment faire dans le Flask Mega Tutorial
* Login students : décider si remplissage des formulaires en vérifiant le mail ou non (pour garantir unicité et existence)
* Textblob : non traité pour l'instant, à revoir

## ORM
Doc : 
* https://docs.sqlalchemy.org/en/13/orm/tutorial.html donne une présentation des méthodes de l'ORM
* https://flask-sqlalchemy.palletsprojects.com/en/2.x/ présente le wrapper flask-sqlalchemy
* https://docs.sqlalchemy.org/en/13/orm/session_basics.html#session-faq-whentocreate

Conclusion à la lecture des docs :
* utilisation de l'ORM (capable de faire suffisamment et notamment de passer du texte SQL en dernier recours)
* utilisation du wrapper flask-sqlalchemy puisque la doc
https://docs.sqlalchemy.org/en/13/orm/session_basics.html#session-faq-whentocreate 
mentionne que SQLAlchemy recommende d'utiliser flask-sqlalchemy, notamment pour éviter le 
problème de la décision de la création d'une Session
* pas d'utilisation des migrations qui n'ajoutent rien d'utile

## Login gestionnaire
Arguments :
* Supprime la nécessité de coder l'url de connexion dans le fichier de conf
* Ajoute une page de login
* N'est nécessaire que dans le cas d'un BD non SQLite
* Repousse la création de sqlalchemy.engine hors de l'initialisation
* Entraîne un traitement différent de l'accès à l'API Google (par fichier
 credentials) et de l'accès à la BD, or c'est la même chose essentiellement

Conclusion :
* Pas utilisé

## Login students
Arguments :
* Juste une case à cocher dans le formulaire Google Form
* Garantit l'unicité des réponses d'un étudiant et son identification 
(pas de problème de nom / prénom en double, ni surtout d'erreur de frappe)
* Négatif : tests plus complexes (créer des adresses mail gmail multiples ?)
* TIP création d'adresses multiples sur le même compte : 
http://www.codestore.net/store.nsf/unid/BLOG-20111201-0411

Conclusion :
* utilisation de ces logins

## Textblob

???

## Problèmes

* https://github.com/pallets/flask/issues/3327, solution lancer flask
avec "set FLASK_DEBUG=1 && python -m flask run"