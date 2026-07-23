# Contexte : préparer l'arborescence de release avant le premier déploiement

L'équipe de dev livre **myapp** sur **web1.lab** jeudi et attend un système de
fichiers prêt : un répertoire de release versionné, un lien `current` que le
service lit, et un répertoire de logs dans lequel l'application écrit sans
tourner en root. La tentative manuelle précédente a laissé traîner un
`/etc/myapp-old.conf` que l'application charge encore. Vous préparez le terrain
depuis **control-node.lab**, dans un playbook qui sera rejoué à chaque release.

Votre mission :

1. Construire l'arborescence sur **web1.lab** : **`/opt/myapp/releases/v1.0.0`**
   (mode `0755`, root) et **`/opt/myapp/shared/logs`** (mode `0750`, propriété
   de `nobody`) pour que l'application écrive ses logs sans privilèges.
2. Faire pointer **`/opt/myapp/current`** vers la release `v1.0.0`, en
   **écrasant** un lien qui viserait déjà ailleurs.
3. Supprimer le résidu **`/etc/myapp-old.conf`** et poser le marqueur d'init
   **`/var/log/myapp-init.timestamp`** (mode `0644`).

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-file/
