# Contexte : « pourquoi mon tag ne s'applique pas aux tâches incluses ? »

Le playbook a atteint quatre cents lignes, alors il a été découpé en fichiers
de tâches. Et là, les choses sont devenues étranges : les tags ont cessé de
sélectionner ce que tout le monde attendait, un fichier devait tourner une
fois par environnement et refusait catégoriquement de boucler, et
`--list-tasks` n'affichait plus que la moitié du plan. Rien n'est cassé.
Ansible a deux façons de tirer un fichier : l'une résolue avant le démarrage
du run, l'autre au fil de son déroulement. Et elles ne se comportent pas
pareil. Vous séparez les deux sur `db1.lab`, depuis **control-node.lab**.

Votre mission :

1. Tirer un ensemble de tâches figé en **statique**, parsé avant même que le
   play ne commence, et le voir apparaître dans le plan.
2. Tirer un second fichier en **dynamique**, une fois par élément d'une boucle,
   et découvrir pourquoi la forme statique en est tout simplement incapable.
3. Poser les bons chemins : un fichier de tâches se résout **relativement au
   playbook**, pas au répertoire où vous vous trouvez.
4. Prouver que les deux mécanismes ont tourné : le marqueur statique sur db1,
   plus un marqueur par itération.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/import-include/
