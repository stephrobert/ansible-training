# Contexte : collecter l'inventaire OS avant la fenêtre de migration

La direction veut savoir exactement quelle version de distribution tourne sur
chaque serveur avant de valider le plan de migration, et « j'ai vérifié, ils
sont tous pareils » ne vaut pas preuve. Il vous faut le `/etc/os-release` brut
de chaque managed node, rangé sur **control-node.lab** sous un nom prévisible,
prêt à être comparé et joint au plan. Des captures d'écran de sessions SSH ne
font pas un inventaire : la collecte doit être rejouable quand le parc
grossira.

Votre mission :

1. Rapatrier **`/etc/os-release`** depuis **web1.lab** et **db1.lab** vers le
   control node, chacun atterrissant dans un **fichier à plat nommé d'après son
   hostname court** (pas de sous-arbre par hôte, pas de suffixe `.lab`).
2. Marquer **web1.lab** avec un fichier d'identité de lab, puis rapatrier ce
   fichier lui aussi : le même play pousse et récupère.
3. Faire **dériver les chemins de destination de l'inventaire**, et non d'une
   liste de hostnames écrite à la main.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-fetch/
