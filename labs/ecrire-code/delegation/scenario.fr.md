# Contexte : une trace de déploiement, pas une par hôte

Chaque livraison sur **web1.lab** et **web2.lab** laisse une trace locale sur
chaque nœud, et ça, ça marche. Ce qui ne marche pas, c'est la trace
centralisée : l'équipe veut **une** ligne sur **db1.lab** attestant que la
livraison a eu lieu. Aujourd'hui, le playbook l'écrit une fois par webserver,
donc db1 reçoit deux fois le même fichier dans la même seconde. Sur un parc de
quarante nœuds, ce serait quarante fois. Et db1 n'est même pas dans le groupe
`webservers`.

Vous corrigez ça depuis **control-node.lab**, sans ajouter un second playbook.

Votre mission :

1. Depuis un play qui cible `webservers`, déposer un **marqueur local** sur
   chaque hôte, nommé d'après l'hôte lui-même.
2. Écrire la **trace centrale sur `db1.lab`** depuis ce même play, alors que
   db1 appartient à un tout autre groupe.
3. Garantir que cette trace est écrite **exactement une fois** pour tout le
   lot, et non une fois par webserver.
4. Lire la notation `web1.lab -> db1.lab` dans la sortie, puis vérifier
   l'isolation : la trace centrale existe sur db1 et sur aucun webserver.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/delegation/
