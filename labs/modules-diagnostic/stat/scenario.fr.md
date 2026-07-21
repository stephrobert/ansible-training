# Contexte : produire le fichier de preuve que réclame l'auditeur

L'auditeur veut la preuve que les fichiers sensibles de **db1.lab** portent les
bonnes permissions, et « j'ai regardé, c'est bon » ne fait pas preuve. Trois
fichiers sont sur la liste : la base des comptes avec une empreinte qui
permettra à un passage ultérieur de détecter une altération, le fichier shadow
dont le propriétaire doit être root, et la configuration sudo, que sudo lui-même
ignore si son mode s'écarte de 0440. Le rapport doit être produit depuis
**control-node.lab**, rejouable, et ne **rien modifier** sur l'hôte audité.

Votre mission :

1. Collecter l'état des trois fichiers sur **db1.lab** en **lecture seule** : un
   audit qui modifie son sujet n'est pas un audit.
2. Ajouter une **empreinte SHA256** sur la base des comptes, sachant que le
   module n'en calcule pas par défaut et que son algorithme par défaut n'est pas
   celui que vous voulez.
3. Récupérer ce que chaque fichier doit prouver : le **mode** pour les trois, le
   **propriétaire** pour le fichier shadow.
4. Assembler l'ensemble dans un **rapport** lisible sur l'hôte, une entrée par
   fichier.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-stat/
