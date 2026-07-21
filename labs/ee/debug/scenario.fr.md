# Contexte : le build annonce un succès et l'image ne sait pas lancer Ansible

Un collègue vous laisse une recette d'EE et un problème. Le build n'affiche
aucune erreur qui mérite qu'on s'arrête, l'image arrive sur le registre, et le
premier playbook qui tente de l'utiliser meurt aussitôt : il n'y a pas de commande
`ansible` dedans. Plusieurs fautes se cachent dans ces fichiers, et la plus
vicieuse est celle qui n'échoue pas. Le build ne vous ment pas : vous ne lisez pas
la bonne ligne de sa sortie.

Votre mission, depuis le répertoire du projet :

1. Tenter le build de la **recette cassée** telle quelle, verbosité poussée, et
   inspecter l'image obtenue plutôt que de croire son code de retour.
2. Expliquer pourquoi l'image est livrée **sans `ansible-core`** alors que la
   recette le réclame noir sur blanc, et retrouver l'avertissement qui l'annonçait.
3. Débusquer les deux dépendances qui n'existent pas, une collection et une version
   Python, et prouver que chacune manque à la source plutôt que d'accuser le réseau
   ou un proxy.
4. Produire un **jeu de fichiers corrigé**, complété par les dépendances système
   que l'original avait oubliées, le builder, et prouver que l'image contient
   enfin ce qu'elle prétend.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/debug-ee-casse/
