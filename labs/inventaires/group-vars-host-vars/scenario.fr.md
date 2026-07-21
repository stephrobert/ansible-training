# Contexte : trancher le débat sur le port réellement utilisé par l'application

L'équipe tourne en rond depuis deux jours. L'application écoute sur le port
standard partout, sauf sur le tier web qui en utilise un autre, sauf sur
**web1.lab** qui a encore été déplacé pour un conflit que personne n'a
documenté. Trois réponses différentes selon la personne interrogée, et la
variable est répartie sur trois niveaux d'inventaire qui se surchargent. Lire le
YAML ne suffit pas : ce qui tranche, c'est ce qu'Ansible **résout à
l'exécution**, sur chaque hôte, depuis **control-node.lab**.

Votre mission :

1. Répartir le port de l'application sur les **trois niveaux** de l'inventaire :
   la valeur par défaut pour tous, la surcharge du tier web, et la valeur
   spécifique de **web1.lab**.
2. Écrire un play visant **tous les hôtes** qui pose sur chacun un marqueur
   contenant **le port résolu pour cet hôte**, nommé d'après l'hôte lui-même.
3. Prouver la précédence sur les trois managed nodes : **web1.lab** prend sa
   valeur de niveau host, **web2.lab** celle du groupe, et **db1.lab** retombe
   sur la valeur par défaut.
4. Lancer le tout sur l'**inventaire du lab**, sans lequel aucune variable de
   groupe n'est chargée et la démonstration ne prouve rien.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/group-vars-host-vars/
