# Contexte : standardiser la boîte à outils et sortir telnet du serveur

Deux sujets sont arrivés sur votre bureau le même matin. L'équipe d'astreinte
en a assez de trouver **web1.lab** sans éditeur digne de ce nom ni complétion
shell, et le scan de sécurité a signalé le client `telnet`, dont le protocole en
clair n'a rien à faire sur un serveur en 2026. Même play, deux sens opposés :
installer ce qui manque, retirer ce qui ne devrait pas être là. Et comme le parc
Debian arrive au trimestre prochain, le playbook ne doit pas figer le
gestionnaire de paquets RHEL.

Votre mission :

1. Depuis **control-node.lab**, aligner **web1.lab** sur la boîte à outils
   standard (éditeur, complétion shell, vue arborescente) en **une seule
   transaction**, pas une tâche par paquet.
2. Retirer **`telnet`**, et faire prouver l'absence par la base de paquets, pas
   par une commande qui se trouve manquante.
3. Rester **agnostique de la distribution** : le même playbook doit survivre à
   l'arrivée des nœuds Debian sans réécriture vers `apt`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-package/
