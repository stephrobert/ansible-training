# Contexte : quelqu'un a choisi un EE parce qu'il sortait en premier

Le projet s'est standardisé sur un Execution Environment le trimestre dernier,
choisi comme souvent : quelqu'un a trouvé un nom d'image dans un article de blog
et ça marchait. Il pèse deux gigaoctets, embarque des collections que personne
n'utilise, et il manque toujours celle dont vos playbooks ont besoin, qu'un
collègue installe désormais au runtime dans le conteneur, ruinant discrètement
tout l'intérêt de la démarche. Avant de construire le vôtre, il faut savoir dire
ce qu'il y a vraiment dans ces images.

Votre mission, depuis le répertoire du projet :

1. Scripter l'inspection d'un EE : **lister les collections embarquées**, la
   version d'`ansible-core` transportée, les paquets système et la taille réelle.
2. Passer cette inspection sur **trois** EE officiels, l'un orienté création, l'un
   orienté controller, l'un délibérément minimal, et comparer les résultats.
3. Lire la documentation d'un module **telle que l'EE la voit** : ce qui est
   documenté dans l'image est ce que votre playbook pourra réellement appeler.
4. Convertir la comparaison en **choix par cas d'usage** : quel EE pour la
   formation, lequel pour un controller, lequel pour une production sobre, et
   pourquoi.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/lookup-doc/
