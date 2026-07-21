# Contexte : un rôle, deux équipes, deux ports

Le rôle `webserver` fonctionne, mais il fige le port 80. L'équipe base de données
veut maintenant ce même rôle sur **db1.lab**, en écoute sur **8080** : le port 80
est déjà pris par un agent de supervision. Un collègue a voulu éditer les tâches
du rôle ; vous refusez. Un rôle qu'il faut modifier pour le réutiliser n'est pas
un rôle, c'est une copie en sursis. Les réglages appartiennent à l'appelant, les
détails internes non.

Votre mission, depuis **control-node.lab** :

1. Déployer le rôle `webserver` sur **db1.lab** en **surchargeant** son port
   d'écoute à **8080** et ses worker connections à **2048**, depuis le playbook
   uniquement, sans toucher au rôle.
2. Injecter une page d'accueil personnalisée qui porte le nom de l'hôte ciblé.
3. Prouver que la surcharge a bien pris : le port ouvert dans firewalld et la
   configuration générée doivent afficher **8080**, pas la valeur livrée.
4. Établir quelles variables sont faites pour être surchargées et lesquelles
   sont des détails internes que l'appelant ne doit jamais atteindre.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/variables-defaults-vars/
