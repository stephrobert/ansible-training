# Contexte : la commande qui annonce « rien à signaler » avec rc=1

La moitié de l'outillage de **db1.lab** ignore la convention. `grep` retourne 1
quand il ne trouve rien. `diff` retourne 1 quand deux fichiers diffèrent. Le
vérificateur de conformité retourne 1 pour dire « j'ai changé quelque chose ».
Ansible lit tout code retour non nul comme un échec, point final : le play
s'arrête sur une tâche qui a fait exactement ce qu'on lui demandait. Pendant ce
temps, une `command:` en lecture seule se déclare fièrement `changed` à chaque
passage, et votre preuve d'idempotence ne vaut plus rien. Vous apprenez la
vraie sémantique à Ansible, depuis **control-node.lab**.

Votre mission :

1. Lancer sur `db1.lab` une commande qui sort en **rc=1**, et capturer son
   résultat.
2. Redéfinir ce que veut dire **échec** pour cette tâche : 0 et 1 sont des
   issues légitimes, tout ce qui est au-dessus est une vraie erreur.
3. Redéfinir ce que veut dire **changement** : rc=1 est le signal que quelque
   chose a bougé, donc la tâche doit se déclarer `changed`, pas `ok`.
4. Prouver que le play a survécu : la tâche suivante s'exécute et le
   récapitulatif affiche `failed=0`. Puis déterminer laquelle des deux
   conditions Ansible évalue en premier, et pourquoi ça compte.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/failed-when-changed-when/
