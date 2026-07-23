# Contexte : nginx redémarre à chaque run, et personne ne sait ce qui a été livré

Deux plaintes le même matin. La prod : le rôle de déploiement redémarre nginx à
**chaque** exécution et coupe les connexions même quand rien n'a changé. La
conformité : aucune trace ne dit ce qui a été déployé, où, ni sur quel port. Les
deux symptômes ont la même cause : le rôle réagit dans ses `tasks:` et ne
documente rien de lui-même. Les réactions vont dans les handlers, l'identité
dans `meta/`.

Votre mission, depuis **control-node.lab** :

1. Déployer le rôle `webserver` sur **db1.lab** avec un port d'écoute
   personnalisé (**8080**) et une page d'accueil portant le nom de l'hôte.
2. Faire déclencher par ce changement les handlers du rôle : un redémarrage de
   service, un rechargement, et un handler **hors service** qui écrit une trace
   de déploiement.
3. Cette trace doit consigner l'hôte **et** le port réellement appliqué : preuve
   que le handler a lu la valeur surchargée, pas la valeur par défaut.
4. Vérifier que la carte d'identité du rôle (`meta/main.yml`) est complète.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/handlers-meta/
