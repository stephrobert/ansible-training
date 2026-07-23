# Contexte : déployer la bannière légale sur le tier web

L'audit de sécurité s'est terminé sur un constat bloquant : **web1.lab** ouvre
les sessions SSH sans le moindre avertissement légal, alors que la conformité
exige la preuve que l'accès est annoncé comme tracé avant même le shell. Le
même audit demande que chaque hôte s'identifie dans son message du jour. Vous
travaillez depuis **control-node.lab** : rien ne se tape à la main sur le
serveur, la bannière part en playbook pour que les vingt serveurs suivants ne
coûtent qu'un `--limit`.

Votre mission :

1. Pousser le texte de la bannière légale depuis le control node vers
   **`/etc/ssh/banner-rhce`** sur **web1.lab**, propriété de root, lisible par
   tous, avec **sauvegarde** de la version précédente.
2. Écrire le marqueur d'identité du serveur directement dans
   **`/etc/motd-rhce`** en **contenu inline**, sans embarquer un fichier source
   pour trois mots.
3. Garder les deux tâches **idempotentes** : un second passage doit annoncer
   zéro changement.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-copy/
