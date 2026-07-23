# Contexte : la session SSH meurt avant le job

Le job de maintenance nocturne de **db1.lab** dure vingt minutes. Le playbook
qui le lance échoue vers la dixième minute, à chaque fois, sur un tuyau SSH
rompu. Pire : personne ne sait dire si le job est mort avec la connexion ou
s'il continue de tourner sur l'hôte. Maintenir une session SSH ouverte pendant
toute la durée d'une tâche longue n'est pas une stratégie. Ansible a une vraie
réponse : lancer, lâcher, et revenir chercher le résultat.

Vous répétez le pattern depuis **control-node.lab** sur un job volontairement
court.

Votre mission :

1. Lancer une tâche longue sur `db1.lab` **en arrière-plan** et récupérer la
   main immédiatement, sans attendre sa fin.
2. Conserver son **job id** : une tâche lancée sans jamais être vérifiée est
   une tâche dont vous ne verrez jamais l'échec.
3. Interroger ce job avec **`async_status`** jusqu'à ce qu'il se déclare
   terminé, avec assez de tentatives et de délai pour couvrir sa durée réelle.
4. Prouver qu'elle a abouti : le fichier marqueur existe sur `db1.lab` avec le
   contenu attendu, et le récapitulatif est cohérent.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/
