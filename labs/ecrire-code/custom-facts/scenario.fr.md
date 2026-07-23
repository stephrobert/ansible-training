# Contexte : l'hôte qui doit dire à qui il appartient

La moitié du parc n'a pas de propriétaire. Quand une machine déraille à
2 heures du matin, l'ingénieur d'astreinte doit deviner quelle équipe
réveiller, et la seule réponse vit dans une page de wiki vieille d'un an.
L'inventaire ne peut pas aider : il décrit ce qu'Ansible gère, pas ce que la
machine porte. Donc la machine va le dire elle-même, et Ansible le relira à
chaque run, à côté des facts qu'il collecte déjà. Vous commencez par
**db1.lab**, depuis **control-node.lab**.

Votre mission :

1. Déposer sur db1 un **custom fact INI statique** déclarant le projet auquel
   il appartient, sa version, et l'équipe qui en est propriétaire.
2. Déposer un second fact qui est un **script exécutable retournant du JSON** :
   ce qu'aucun fichier statique ne peut savoir, comme le noyau courant et
   l'uptime.
3. Poser les bons modes : un fact statique se lit, un fact dynamique doit être
   **exécutable**. Le mauvais mode est l'échec classique ici, et son message
   d'erreur ne vous aidera pas.
4. Re-collecter les facts, puis relire les deux via **`ansible_local`** et
   écrire le fichier de preuve sur db1.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/custom-facts/
