# Contexte : aligner la numérotation des groupes avant de monter le partage NFS

L'équipe s'apprête à partager un volume entre plusieurs hôtes, et le premier
test s'est mal passé : un fichier écrit sur un serveur revenait illisible sur le
suivant. La cause est identifiée, et elle est classique. Les groupes ont été
créés hôte par hôte avec le GID que le système voulait bien attribuer : le même
nom de groupe porte donc deux numéros différents, alors que le système de
fichiers stocke les droits **par GID**, jamais par nom. Avant la mise en service
du partage, la numérotation se fige depuis **control-node.lab**.

Votre mission :

1. Créer les trois groupes du projet sur **db1.lab** avec leurs **GID
   explicites** (4000, 4001, 4002), pour que la numérotation soit reproductible
   sur tous les hôtes du parc.
2. Piloter les trois créations depuis une **seule tâche**, pas en recopiant
   trois fois le même bloc.
3. Ajouter le **groupe système** de l'application, qui relève de la plage
   réservée sous 1000 et doit laisser le système attribuer son numéro.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-group/
