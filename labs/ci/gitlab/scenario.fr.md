# Contexte : l'entreprise tourne sur GitLab, et une release vient de partir d'une branche

Les rôles de l'équipe ont migré sur le GitLab interne, et l'ancien workflow
GitHub ne se traduit pas. La première tentative a empiré les choses : le job de
publication n'avait aucune condition, et un merge sur une branche de feature a
poussé sur Galaxy une release que personne n'avait validée. Publier n'est pas une
étape d'un pipeline de test. C'est ce qui arrive quand quelqu'un, et seulement
quand quelqu'un, pose délibérément un tag de version.

Votre mission, depuis le répertoire du projet :

1. Découper le pipeline en **trois stages**, lint puis test puis release, pour
   qu'aucun job ne s'exécute avant celui qui aurait pu l'arrêter.
2. Décliner le stage de test sur une **matrice distributions et versions**, en
   parallèle, et mettre les dépendances Python en cache entre les runs.
3. Conditionner le job de release pour qu'il ne se déclenche **que sur un tag
   Git** : jamais sur un push de branche, jamais sur une merge request.
4. Faire publier ce job sur Galaxy avec son token, et tenir ce token hors de
   portée de tous les autres stages.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-gitlab/
