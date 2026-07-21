# Contexte : votre automatisation ne tient plus dans un rôle

L'automatisation partagée de l'équipe a dépassé ce qu'un rôle peut porter. Il y a
un rôle nginx, un module Python écrit par quelqu'un pour contrôler la santé de
l'application, et trois playbooks qui relient le tout, chacun dans son dépôt, avec
sa version, et aucune version de l'ensemble. Les utilisateurs installent trois
choses et espèrent que la combinaison tient. Par ailleurs, la plateforme sur
laquelle l'entreprise publie n'accepte plus du tout les rôles standalone.

Votre mission, depuis **control-node.lab** :

1. Générer une **collection** sous votre namespace et renseigner son manifeste :
   namespace, nom, version, dépendances et tags. Voilà la nouvelle unité versionnée.
2. Y intégrer un **rôle**, et ajouter votre propre **module Python**, avec la
   documentation, les exemples et le bloc de retour qu'un module doit porter.
3. Rendre compte de la structure standard : ce qui va dans plugins, roles,
   playbooks, meta et tests, et pourquoi un module ne se dépose pas n'importe où.
4. **Builder le tarball** et vérifier que la collection passe les contrôles de
   sanity : une collection qui échoue en sanity n'est pas distribuable.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/creer-collection-custom/
