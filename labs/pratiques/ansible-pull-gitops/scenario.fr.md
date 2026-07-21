# Contexte : quatre cents nœuds que votre control node n'atteindra jamais

Le nouveau parc vit dans des boutiques, derrière des box grand public : pas
d'adresse publique, pas de SSH entrant, parfois hors ligne une journée entière.
Votre nœud de contrôle n'en atteint aucun, et le modèle push est au bout du
rouleau. Plus de machine centrale qui ouvre les connexions vers l'extérieur. Si un
nœud veut sa configuration, il devra aller la chercher lui-même, auprès de la seule
chose qu'il peut toujours joindre : un dépôt Git.

Votre mission, depuis le répertoire du projet :

1. Publier la configuration dans un **dépôt Git** et faire en sorte que la cible la
   tire et se l'applique **à elle-même**, sans nœud de contrôle dans la boucle.
2. Prouver l'exécution en faisant déposer au play tiré une preuve sur le nœud qui
   l'a joué, et non sur la machine qui a écrit le playbook.
3. Le rendre **autonome** : planifier le tirage pour que le nœud converge tout seul,
   et faire en sorte qu'une machine fraîchement provisionnée s'amorce au premier
   démarrage.
4. Tracer la limite pour l'équipe : ce que le push fait toujours mieux, ce que le
   pull apporte en périphérie ou à quatre cents nœuds, et ce qu'on cède en échange.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/pratiques/ansible-pull-gitops/
