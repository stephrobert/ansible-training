# Contexte : durcir la config de l'application sans toucher aux voisins

L'application de **db1.lab** lit `/etc/myapp.conf`, et trois changements
tombent en même temps : l'API déménage sur un nouveau domaine derrière TLS,
le port de service passe à 8443, et SSL doit être activé. Le piège est écrit
dans le fichier lui-même : il empile une section `[server]` et une section
`[client]`, et toutes deux déclarent `ssl_enabled=false`. Seul le côté
serveur doit basculer à `true` : une substitution aveugle basculerait aussi
le client et casserait sa négociation. Vous intervenez depuis
**control-node.lab**, sur un fichier qui doit ressortir modifié au scalpel.

Votre mission :

1. Faire passer l'URL de l'API en **https sur son nouveau domaine**, partout
   où elle apparaît, en gardant le chemin intact.
2. Monter le **port à 8443** en préservant le préfixe `port=`, plutôt que de
   réécrire toute la ligne.
3. Activer SSL **dans la seule section `[server]`**, en **bornant la zone de
   substitution** plutôt qu'en faisant confiance au motif.
4. Prouver que les dégâts collatéraux sont nuls : `[client]` affiche toujours
   `ssl_enabled=false`, et un second passage ne change rien.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-replace/
