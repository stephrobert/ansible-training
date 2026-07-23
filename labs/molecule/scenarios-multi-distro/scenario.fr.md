# Contexte : le rôle part en public et ne connaît que RHEL

Votre rôle `webserver` va être publié, et la première issue est déjà prévisible.
Il appelle `dnf` en direct, écrit dans `/usr/share/nginx/html` et suppose que le
service tourne sous l'utilisateur `nginx`. Sur Debian, le gestionnaire de paquets
est faux, la racine web est ailleurs et l'utilisateur s'appelle `www-data`. Le
rôle ne fonctionne nulle part ailleurs, et pire : la suite de tests n'a aucun
moyen de s'en apercevoir, elle n'a jamais testé que la distribution de l'auteur.

Votre mission, depuis le répertoire du projet :

1. Étendre la matrice de test à **trois distributions** couvrant au moins deux
   familles d'OS, pour que la suite échoue le jour où la portabilité casse.
2. Sortir des tâches les faits divergents (nom du paquet, racine web,
   utilisateur du service) vers des **fichiers de variables par OS**, chargés
   d'après la famille détectée sur la cible.
3. Remplacer les appels de paquets spécifiques par le module **agnostique**,
   pour que le rôle cesse de choisir le gestionnaire à la place de l'appelant.
4. Vérifier que le **même** rôle, inchangé, converge sur les trois plateformes.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-scenarios-multi-distro/
