# Contexte : transformer le disque partitionné en stockage utilisable

Le disque de **db1.lab** est partitionné mais reste inutile : des partitions sans
système de fichiers ne contiennent rien. Deux besoins à couvrir. La partition de
données doit porter le système de fichiers que l'éditeur de la base recommande
pour ses gros fichiers, et la petite partition devient le swap qui manque à la
machine depuis le dernier OOM kill. Les deux doivent revenir **d'eux-mêmes après
un reboot** : un swap activé à la main et un volume monté à la main disparaissent
au redémarrage suivant, en silence.

Votre mission :

1. Depuis **control-node.lab**, créer le **système de fichiers xfs** sur la
   partition de données de **db1.lab**, et préparer la petite partition **en
   swap**.
2. **Activer le swap maintenant** et l'inscrire dans `/etc/fstab`, en gardant à
   l'esprit qu'un swap ne se monte pas sur un répertoire comme un système de
   fichiers ordinaire.
3. **Monter la partition de données** sur son point de montage, avec sa propre
   entrée fstab.
4. Prouver les deux : le swap apparaît actif, le point de montage annonce xfs, et
   le second passage affiche `changed: 0`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-filesystem/
