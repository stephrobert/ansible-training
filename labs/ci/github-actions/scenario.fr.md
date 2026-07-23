# Contexte : le rôle est public, des inconnus vont proposer des patches

Votre rôle `webserver` est open source. La première contribution extérieure
arrive demain, et vous ne la jouerez pas à la main : vous n'avez ni confiance
dans ce code ni le temps, et personne ne veut être celui qui a oublié de tester
une distribution. Pire : un workflow qui clone le dépôt et exécute du code non
vérifié avec un token en écriture, c'est ainsi qu'un rôle devient un vecteur
d'attaque. La barrière doit être automatique, et sûre même sur la branche d'un
contributeur.

Votre mission, depuis le répertoire du projet :

1. Faire passer chaque push et chaque merge request par **deux barrières** : le
   lint d'abord, le cycle Molecule ensuite, pour qu'une faute de style ne brûle
   jamais des minutes de matrice.
2. Décliner le job de test sur une matrice **distributions x versions
   d'`ansible-core`**, jouée en parallèle.
3. Mettre en cache l'installation des dépendances Python, pour que le pipeline
   reste assez rapide pour qu'on l'attende vraiment.
4. Verrouiller le workflow : **permissions minimales** sur le token, et aucun
   identifiant laissé derrière le checkout pour les étapes suivantes.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-github-actions/
