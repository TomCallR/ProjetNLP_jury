# ProjetNLP_jury
Version définitive du projet NLP

Trois points importants à revoir

* BDD : utilisation ORM ou non
* Login : décider si remplissage des formulaires en vérifiant le mail ou non (pour garantir unicité et existence)
* Textblob : non traité pour l'instant, à revoir

## ORM
Doc : 
* https://docs.sqlalchemy.org/en/13/orm/tutorial.html donne une présentation des méthodes de l'ORM
* https://flask-sqlalchemy.palletsprojects.com/en/2.x/ présente le wrapper flask-sqlalchemy

Conclusion à la lecture des docs :
* utilisation de l'ORM (capable de faire suffisamment e notamment de passer du texte SQL en dernier recours)
* utilisation de l'ORM purement Sqlalchemy, non du wrapper flask-alchemy
* pas d'utilisation des migrations qui n'ajoutent rien d'utile

## Login

???

## Textblob

???