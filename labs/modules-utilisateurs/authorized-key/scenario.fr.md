# Contexte : distribuer des accès SSH sans distribuer le serveur entier

L'authentification par mot de passe part à la retraite sur **db1.lab**, et trois
accès doivent atterrir avant sa disparition : Alice travaille de partout et a
besoin d'une clé ordinaire ; Bob ne se connecte jamais que depuis le sous-réseau
du bureau, et la sécurité veut que sa clé ne serve à rien ailleurs ; le robot de
sauvegarde a besoin de son propre compte, mais une clé de robot qui ouvre un
shell interactif, c'est un double des accès admin qui dort dans un runner de CI.
Tout se provisionne depuis **control-node.lab**.

Votre mission :

1. Créer les deux comptes utilisateurs sur **db1.lab**, puis installer la **clé
   personnelle d'Alice**, sans restriction.
2. Installer la **clé de Bob restreinte au sous-réseau du bureau**, sans
   allocation de terminal.
3. Donner au robot de sauvegarde une clé qui ne peut **que déclencher le script
   de sauvegarde** : pas de shell, pas de tunnels, pas de renvoi X11. Une clé
   interceptée ne doit rien valoir.
4. Ajouter les clés **sans effacer** celles déjà en place : verrouiller le
   formateur hors de la machine ne fait pas partie de l'exercice.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-authorized-key/
