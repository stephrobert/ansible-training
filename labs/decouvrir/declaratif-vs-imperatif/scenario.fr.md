# Contexte : le script qui ajoute une ligne toutes les nuits

Un collègue déploie la page d'accueil de **web1.lab** avec un script Bash
lancé par cron. Ça marche. Sauf que les visiteurs lisent maintenant trois fois
« Servi par web1.lab » sur la page, puis quatre, puis cinq. Personne n'a
touché à la page : le script ajoute la ligne à chaque passage et ne se demande
jamais si elle est déjà là. L'incident est petit, la leçon ne l'est pas.

Depuis **control-node.lab**, vous allez voir pourquoi le même travail, écrit
en déclaratif, ne peut pas dériver.

Votre mission :

1. Jouer **trois fois le script Bash** sur `web1.lab` et regarder le compteur
   de lignes grimper : la dérive, en direct.
2. Réinitialiser le nœud, puis jouer **trois fois le playbook** et constater
   que la page reste à exactement une ligne.
3. Lire le second `PLAY RECAP` : **`changed=0`** est la preuve mécanique de
   l'idempotence, pas une affaire d'opinion.
4. Comparer les deux fichiers et nommer ce que le module `lineinfile:` compare avant
   d'écrire quoi que ce soit.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/declaratif-vs-imperatif/
