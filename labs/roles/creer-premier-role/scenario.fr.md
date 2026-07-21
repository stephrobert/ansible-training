# Contexte : arrêter de copier-coller le même playbook web

Votre équipe déploie ses serveurs web en recopiant les mêmes vingt tâches dans
chaque nouveau playbook. La semaine dernière, une règle de pare-feu a été
corrigée dans une copie et oubliée dans les quatre autres : un hôte est parti en
production avec HTTP fermé. Le lead a tranché : tout ce qui est réutilisable
devient un **rôle**. Un rôle `webserver` existe déjà comme modèle, on vous l'a
donné tout fait, et une nouvelle application interne réclame un serveur web sur
**db1.lab**. Cette fois, le rôle, c'est vous qui l'écrivez.

Votre mission, depuis **control-node.lab** :

1. Générer un rôle **`nginx-server`** avec la structure standard : `tasks/`,
   `defaults/`, `handlers/`, `meta/` et un `README.md`.
2. Lui faire installer **nginx**, le démarrer, l'activer au boot et ouvrir HTTP
   dans firewalld de façon **persistante**, sans casser l'idempotence.
3. Exposer une valeur surchargeable dans `defaults/main.yml` et brancher un
   handler **`Restart nginx`** déclenché par `notify:`.
4. Appeler le rôle depuis un playbook qui ne cible que **db1.lab**.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/creer-premier-role/
