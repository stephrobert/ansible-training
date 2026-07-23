# Contexte : appliquer la baseline de durcissement kernel au serveur de base

La baseline de sécurité atterrit sur **db1.lab** avec quatre réglages kernel à
régler. La machine doit router le trafic du sous-réseau backend, survivre à un
SYN flood, cesser d'exposer les pointeurs kernel via `/proc` à n'importe quel
utilisateur local, et arrêter de swapper une base de données qui a largement
assez de RAM. Deux contraintes encadrent le travail. Les réglages doivent être
**actifs maintenant**, car redémarrer une base de production pour appliquer un
paramètre n'est pas une option, et ils doivent malgré tout **survivre au
reboot**.

Votre mission :

1. Depuis **control-node.lab**, poser les quatre paramètres de la baseline sur
   **db1.lab** : routage IPv4, SYN cookies, restriction des pointeurs kernel et
   réticence au swap.
2. Les écrire tous dans un **fichier dédié sous `/etc/sysctl.d/`**, pas dans la
   configuration globale dépréciée : un rôle possède son fichier et reste
   versionnable.
3. Les faire **appliquer immédiatement**, sans attendre un reboot.
4. Piloter les quatre paramètres depuis une **seule tâche**, et confirmer que le
   second passage n'annonce aucun changement.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-sysctl/
