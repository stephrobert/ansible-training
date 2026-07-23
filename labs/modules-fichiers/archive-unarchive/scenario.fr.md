# Contexte : prouver que la chaîne de sauvegarde et de restauration fonctionne

**db1.lab** porte un répertoire de données qui n'a jamais été sauvegardé, et le
plan de reprise affirme que la procédure de restauration est « documentée ».
Personne ne l'a jamais exécutée. Votre responsable veut la chaîne complète
démontrée de bout en bout avant l'audit : produire une archive, la restaurer
ailleurs, et montrer que les deux côtés concordent. Le tout doit tourner depuis
**control-node.lab**, en playbook qu'un cron pourrait rejouer chaque nuit sans
malmener le disque.

Votre mission :

1. Mettre en place les données source sur **db1.lab** dans `/opt/data-source/`,
   puis en produire l'archive compressée **`/opt/backup/data.tar.gz`**.
2. Restaurer cette archive dans **`/opt/restored/`**, en gardant à l'esprit que
   l'archive se trouve **sur le managed node**, pas sur votre control node.
3. Rendre l'extraction **idempotente** : le second passage doit **skipper** la
   restauration au lieu de réécrire les fichiers et de bousculer tous les mtime.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/archive-unarchive/
