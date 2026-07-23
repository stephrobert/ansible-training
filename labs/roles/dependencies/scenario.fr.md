# Contexte : tout le monde oublie les prérequis

Chaque playbook qui utilise le rôle `webserver` commence par les deux mêmes
corvées : mettre SELinux dans le bon mode avec les bons booléens, puis ouvrir les
ports dans firewalld. Celui qui en oublie une obtient un serveur web qui démarre
et ne sert rien, et y passe l'après-midi. Ces prérequis ne regardent pas
l'appelant : le rôle sait ce dont il a besoin, il doit donc le dire une fois
pour toutes et être obéi.

Votre mission, depuis le répertoire du projet, contre **db1.lab** :

1. Faire **déclarer** au rôle `webserver` les deux rôles dont il dépend,
   `selinux_setup` puis `firewall_setup`, pour qu'aucun appelant ne puisse plus
   les sauter.
2. Passer à chaque dépendance les variables qui lui sont propres : SELinux en
   `enforcing`, et le **443/tcp** ouvert par le rôle pare-feu, sans polluer le
   rôle parent.
3. Écrire un play qui ne consomme **que** le rôle `webserver`, à l'écoute sur
   8081, et prouver l'ordre d'exécution réel sur la cible : chaque rôle
   consigne son passage dans `/tmp/deps-order.txt`, et ce fichier doit se lire
   dépendances d'abord, rôle parent en dernier.
4. Affronter le diamant : quand deux dépendances en partagent une troisième,
   trancher combien de fois ce rôle commun s'exécute, et ce qui change la
   réponse.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/dependencies/
