# Contexte : la tâche de reset qui ne doit jamais partir toute seule

Le playbook de `db1.lab` fait trois choses : un contrôle préalable, la
configuration de routine, et il embarque une routine de **reset** qui remet
l'état de l'hôte à zéro. Cette dernière est légitime : quelqu'un en a besoin
quand un nœud est reconstruit. Sauf qu'elle vit dans le même fichier, et
qu'elle est déjà partie une fois, déclenchée par un ingénieur fatigué qui
voulait seulement pousser un changement de config. Vous n'allez pas découper
le fichier : vous allez rendre le reset inatteignable sauf demande nominative,
depuis **control-node.lab**.

Votre mission :

1. Taguer la tâche de configuration de routine pour qu'un run
   `--tags configuration` la touche, elle et rien d'autre.
2. Faire tourner le marqueur de contrôle préalable **quoi que** demande
   l'opérateur, grâce au tag `always`.
3. Verrouiller le reset destructif derrière **`never`**, à côté de son propre
   tag `reset` : ignoré par défaut, ignoré même sur un run sans option,
   joignable uniquement sur demande explicite.
4. Vérifier en lançant avec `--tags configuration` : les marqueurs `always` et
   `configuration` sont là, celui du reset ne l'est pas.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/tags/
