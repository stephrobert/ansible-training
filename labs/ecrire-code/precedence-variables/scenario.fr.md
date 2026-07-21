# Contexte : « j'ai changé la valeur et il ne se passe rien »

Deux heures perdues hier. Un collègue a posé la valeur dans le fichier de
vars, lancé le playbook sur **db1.lab**, et récupéré l'ancienne. Il l'a posée
à nouveau, dans un autre fichier : même résultat. Il a fini par modifier le
play lui-même, exactement ce que personne ne veut voir dans le dépôt. Ansible
résout un même nom de variable à travers **vingt-deux niveaux**, et il n'y a
là rien de mystérieux : soit vous connaissez l'ordre, soit vous y passez vos
après-midi. Vous tranchez expérimentalement, depuis **control-node.lab**.

Votre mission :

1. Déclarer la **même variable** dans les `vars:` du play et dans un fichier
   chargé par `vars_files:`.
2. Lancer sans rien passer et enregistrer la valeur résolue sur db1 :
   `vars_files:` (niveau 14) **gagne** contre les `vars:` du play (niveau 12),
   tout l'inverse de l'intuition.
3. Écraser les deux depuis la ligne de commande avec **`--extra-vars`** et
   regarder le niveau le plus haut l'emporter sur tout le reste.
4. Expliquer le résultat plutôt que l'apprendre par cœur : pourquoi
   `--extra-vars` est le bon outil d'une surcharge ponctuelle, et le mauvais
   d'un réglage permanent.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/
