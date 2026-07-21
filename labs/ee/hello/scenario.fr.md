# Contexte : le playbook que seul votre poste sait exécuter

La mise en production a échoué à 2h du matin et l'astreinte n'a pas pu prendre le
relais. Le playbook tourne sur votre machine et sur elle seule : vous avez une
collection installée que personne d'autre n'a, une bibliothèque Python épinglée par
accident il y a trois mois, et une version d'`ansible-core` qui ne correspond plus
à celle du runner de CI. Chaque passage de main finit pareil : une page de wiki qui
liste les prérequis, et un collègue bloqué au milieu. Le runtime doit voyager avec
le playbook.

Votre mission, depuis le répertoire du projet :

1. Tirer une image **Execution Environment** officielle avec Podman : tout le
   runtime Ansible devient un artefact versionné au lieu d'une page de wiki.
2. Le déclarer comme **environnement par défaut** du projet, et scripter la
   vérification des prérequis pour qu'un nouvel arrivant démarre sans rien demander.
3. Lancer un playbook **dans** l'EE contre **web1.lab** et **db1.lab**, et prouver
   que le conteneur atteint les managed nodes aussi bien qu'un run local.
4. Comparer les deux exécutions, classique et conteneurisée, et nommer ce qui a
   réellement changé : ce qui est désormais garanti, et ce que cela coûte.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/presentation/
