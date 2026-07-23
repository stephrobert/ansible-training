# Contexte : nginx annonce son numéro de version à toute la planète

Le rapport de pentest est revenu avec deux remarques qui ne coûtent rien à
corriger et qui traînent depuis un an : **db1.lab** répond à chaque requête
HTTP avec sa version exacte de nginx dans l'en-tête `Server`, et signe ses
pages d'erreur des mêmes détails. De la reconnaissance offerte à qui scanne la
plage. Second point du rapport : les réponses ne portent aucun en-tête
`X-Content-Type-Options`, et laissent donc les navigateurs deviner eux-mêmes le
type des contenus servis. Changer la configuration, c'est deux lignes. La faire
prendre effet **sans redémarrer nginx à chaque passage du playbook**, et
laisser une trace pour l'audit, voilà le vrai travail. Vous opérez depuis
**control-node.lab**.

Votre mission :

1. Sur `db1.lab`, durcir la configuration de `nginx` pour qu'il cesse
   d'annoncer sa version, puis lui faire refuser le MIME sniffing.
2. Faire **notifier deux handlers** par la tâche de durcissement : le
   rechargement, et une entrée horodatée dans un journal local que les
   auditeurs pourront lire.
3. Préférer un **reload** à un restart, et forcer les handlers à tourner dans
   le même play pour vérifier l'effet immédiatement.
4. Le prouver de l'extérieur : l'en-tête `Server` doit valoir exactement
   `nginx`, sans version, la réponse doit porter `X-Content-Type-Options:
   nosniff`, et un second passage ne doit notifier personne.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/handlers/
