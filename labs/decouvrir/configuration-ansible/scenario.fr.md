# Contexte : quel ansible.cfg tourne vraiment ?

Le même playbook met quatre minutes chez vous et onze chez votre collègue, et
aucun de vous deux ne sait quel `ansible.cfg` Ansible a réellement lu : celui
de `/etc`, celui du répertoire personnel, celui de la racine du dépôt, ou une
variable d'environnement qui écrase tout en silence. Pire : personne ne peut
dire quelle tâche mange les onze minutes. On arrête de deviner. Vous
travaillez depuis **control-node.lab** et archivez la preuve sur `db1.lab`.

Votre mission :

1. Écrire un **`ansible.cfg` projet** qui monte le parallélisme à
   **`forks = 20`**, bascule la sortie sur le **callback `yaml`** et active
   **`profile_tasks`** pour que les tâches lentes se dénoncent elles-mêmes.
2. Vérifier ce qui est **réellement actif** avec
   `ansible-config dump --only-changed`, et comprendre pourquoi votre fichier
   ne gagne que si le run démarre depuis son répertoire.
3. Archiver la preuve : déposer ce dump sur `db1.lab` dans
   `/tmp/lab03a-config.txt`, propriétaire `root`, mode `0644`.
4. Garder la capture honnête : une commande qui ne fait que lire ne doit jamais
   se déclarer `changed`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/ansible-config-fichier/
