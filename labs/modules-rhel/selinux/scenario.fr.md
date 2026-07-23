# Contexte : servir l'application depuis un dossier custom, SELinux toujours actif

L'application déployée sur **db1.lab** vit en dehors de la racine web par
défaut, et nginx renvoie 403 sur chaque fichier alors que les permissions sont
correctes. Elle doit aussi joindre une API backend, et ces appels sortants sont
refusés eux aussi. Un collègue a appliqué le correctif le plus rapide : SELinux
désactivé. Ce n'est pas un correctif, c'est un constat au prochain audit, et
l'examen RHCE le note comme un échec. Vous remettez la protection et faites
fonctionner l'application **avec**, depuis **control-node.lab**.

Votre mission :

1. Installer les prérequis SELinux sur **db1.lab**, sans lesquels les modules
   échouent sur une erreur peu parlante, puis remettre SELinux en **enforcing**
   sous la politique targeted.
2. Autoriser les **connexions réseau sortantes** du serveur web via le bon
   booléen, avec **persistance** : un booléen qui retombe au reboot ne corrige
   rien.
3. Déclarer le bon **contexte de fichier sur le répertoire applicatif custom**,
   sous forme de motif couvrant toute l'arborescence, pas seulement le dossier.
4. **Appliquer ce contexte aux fichiers déjà présents** : le déclarer dans la
   politique les laisse intacts, et nginx continue de renvoyer 403.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-selinux/
