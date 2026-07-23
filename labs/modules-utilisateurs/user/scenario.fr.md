# Contexte : accueillir la nouvelle équipe sur le serveur de base de données

Deux personnes rejoignent le projet lundi et la chaîne de déploiement a besoin
de sa propre identité sur **db1.lab** : Alice prend le rôle d'admin et doit
atteindre sudo, Bob travaille comme développeur, et un compte de service exécute
les déploiements depuis un répertoire applicatif plutôt qu'un home classique. Le
partage NFS que l'équipe montera lit les permissions **par UID** : les comptes
techniques doivent donc porter les mêmes numéros sur tous les hôtes. Vous
provisionnez depuis **control-node.lab**.

Votre mission :

1. Créer d'abord le **groupe de l'équipe** sur **db1.lab**, puis les trois
   comptes qui en dépendent : l'ordre n'est pas négociable.
2. Donner à Alice ses privilèges d'admin via le **groupe secondaire** qui ouvre
   sudo, **sans lui retirer** les groupes auxquels elle appartient peut-être
   déjà.
3. Figer les **UID fixes** sur les deux comptes techniques, et donner au compte
   de déploiement son home dans le répertoire applicatif plutôt que dans
   `/home`.
4. Vérifier que l'ensemble est **idempotent** : un compte conforme doit
   afficher `ok`, jamais `changed`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-user/
