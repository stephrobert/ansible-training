# Contexte : une page d'état sur db1, et SELinux qui dit non

L'équipe supervision veut un petit endpoint HTTP sur **db1.lab**. Le port 80
est exclu sur cet hôte : ce sera donc le **8888**. Trivial, jusqu'à la
première tentative : `nginx` refuse de démarrer, le log dit « bind() to
0.0.0.0:8888 failed (13: Permission denied) », et rien n'est faux dans la
configuration. Bienvenue sur RHEL : un port non standard n'est pas qu'une
affaire de pare-feu, SELinux aussi a son mot à dire.

Vous écrivez tout ça depuis **control-node.lab**. Personne ne se connecte sur
db1 pour bricoler à la main.

Votre mission :

1. Installer **`nginx`** sur `db1.lab`, démarré et activé au boot.
2. Le faire écouter sur **8888** au lieu de 80, et faire accepter ce port par
   **SELinux** plutôt que de le laisser tuer le service en silence.
3. Ouvrir le **8888** dans firewalld pour que la règle s'applique tout de
   suite **et** survive à un redémarrage.
4. Servir la page d'accueil exacte demandée par le challenge, au caractère
   près, puis lire le `PLAY RECAP` d'un second passage : il doit afficher
   `changed=0`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premier-playbook/
