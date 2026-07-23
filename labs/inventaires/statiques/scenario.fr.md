# Contexte : il n'y a pas encore d'inventaire, et rien ne tourne sans lui

Les autres labs d'inventaire vous fournissaient un `hosts.yml` tout prêt et vous
laissaient jouer avec les patterns et les variables. Dans la vraie vie, et le
jour de l'examen, personne ne vous donne ce fichier : c'est vous qui l'écrivez.
La toute première tâche de l'examen blanc RHCE est « créer l'inventaire statique
des hôtes », et chaque playbook que vous lancerez le lit. Un inventaire absent,
ou qui range le mauvais hôte dans le mauvais groupe, fait viser les mauvaises
machines à toutes les tâches suivantes.

Vous êtes sur **control-node.lab**, face à trois nœuds gérés : deux serveurs web
(**web1.lab**, **web2.lab**) et un serveur de base de données (**db1.lab**).
Aucun inventaire n'existe.

Votre mission :

1. Écrire un **inventaire statique de zéro**, à la main, sans générateur.
2. Déclarer deux groupes d'hôtes : **`webservers`** (web1 + web2) et
   **`dbservers`** (db1).
3. Déclarer un **groupe parent** `datacenter` qui les agrège tous les deux, via
   **`children`**.
4. Ajouter des **variables de groupe** : une propre à `webservers`, une portée
   par le parent `datacenter` pour que chaque hôte en hérite.
5. Ne jamais coder d'adresse IP en dur : la connexion passe par le `ssh_config`
   de dsoxlab, et l'utilisateur SSH est `student`.

Vous ne prouvez rien en montrant le fichier. Vous le prouvez en demandant à
Ansible ce qu'il résout (`ansible-inventory --list`) et en joignant exactement
les bons hôtes (`ansible <groupe> -m ping`).

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/statiques-yaml/
