# Contexte : trois nœuds neufs, rien d'autre qu'une clé

Le provisionnement vient de vous livrer **web1.lab**, **web2.lab** et
**db1.lab**. Cloud-init a fait le strict minimum : un utilisateur `ansible`,
une clé SSH, sudo sans mot de passe. Rien de plus. Leurs horloges divergent
déjà, ils ne se résolvent pas entre eux par leur nom, et l'état de SELinux est
une inconnue. Tous les playbooks de la formation vont tourner dessus : elles
doivent d'abord être **identiques et prévisibles**. Depuis
**control-node.lab**, vous écrivez le bootstrap qui fait qu'Ansible prépare
lui-même son parc.

Votre mission :

1. Converger les **prérequis de base** sur les trois managed nodes : les
   paquets Python dont les modules ont besoin, et `chrony` actif pour que les
   facts partagent une seule horloge.
2. Faire en sorte que chaque nœud **résolve** `web1.lab`, `web2.lab`,
   `db1.lab` et `control-node.lab`.
3. Figer la ligne de base : **SELinux en enforcing** avec la policy `targeted`,
   fuseau horaire **Europe/Paris**.
4. Prouver que c'est un **bootstrap et non un script** : un second passage doit
   afficher `changed=0` sur les trois nœuds.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/preparer-noeuds-geres/
