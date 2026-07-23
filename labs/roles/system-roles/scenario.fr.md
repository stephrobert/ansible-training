# Contexte : le fichier que personne n'aurait dû écrire

L'audit a rendu son rapport. Sur db1.lab, l'horloge dérive, les serveurs NTP
sont ceux que le DHCP a bien voulu pousser, et le `/etc/chrony.conf` en place
porte trois générations de commentaires contradictoires. Le collègue qui l'avait
« corrigé à la main la dernière fois » est parti depuis. Personne n'ose y
toucher, parce que personne ne sait ce qui casse si on y touche.

Red Hat a déjà écrit ce que vous alliez réécrire. Le rôle système `timesync`
prend une intention en variables et rend un fichier généré, signé, cohérent, sur
toutes les versions de RHEL. C'est un objectif de l'EX294 à part entière, et
c'est aussi la seule façon de rendre ce fichier réparable par le prochain.

Votre mission, depuis le répertoire du projet, contre **db1.lab** :

1. Consommer le rôle système **`timesync`** au niveau du play, en nom pleinement
   qualifié. Vous ne devez écrire **aucune ligne** de `chrony.conf` vous-même.
2. Déclarer **trois serveurs NTP** : `0.fr.pool.ntp.org` en source préférée,
   `1.fr.pool.ntp.org`, et `2.fr.pool.ntp.org` bridé à un intervalle
   d'interrogation maximal. Tous les trois en `iburst`.
3. Ramener le **seuil de correction brutale** de l'horloge à 0,1 seconde, et
   exiger que **deux sources** soient d'accord avant tout ajustement.
4. Faire disparaître ce que la distribution avait posé : le `pool` par défaut et
   la porte ouverte du DHCP.
5. Le prouver sur la machine, pas dans votre éditeur : `chronyd` doit tourner
   avec ces trois sources, et l'horloge doit être verrouillée sur l'une d'elles.

Le play doit être **idempotent** : rejoué, il ne réécrit rien et ne redémarre
rien.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/
