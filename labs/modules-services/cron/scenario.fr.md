# Contexte : planifier la sauvegarde et le nettoyage qui n'ont jamais tourné

La partition `/tmp` de **db1.lab** a saturé dimanche et a emporté la base avec
elle, tandis que la sauvegarde horaire que tout le monde croyait active ne
figurait dans la crontab de personne. Les deux jobs doivent être planifiés, et
surtout **auditables** : l'administrateur précédent éditait une crontab
partagée à la main, et personne ne sait aujourd'hui qui a ajouté quoi. Vous
passez à un fichier dédié et versionné, déployé depuis **control-node.lab**, et
les échecs doivent atteindre un humain.

Votre mission :

1. Provisionner un **fichier qui vous appartient dans `/etc/cron.d/`** sur
   **db1.lab**, plutôt que de patcher la crontab partagée, pour qu'un rôle
   possède sa planification.
2. Poser l'**adresse de notification** en tête de ce fichier, pour qu'un job en
   échec écrive à quelqu'un au lieu de mourir en silence.
3. Planifier les deux jobs en root : la **sauvegarde horaire** et le
   **nettoyage quotidien à 3 h** des fichiers de `/tmp` vieux de plus d'une
   semaine.
4. Garantir l'**idempotence** : rejouer le playbook ne doit pas empiler une
   seconde copie de chaque job.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-cron/
