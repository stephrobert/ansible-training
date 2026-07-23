# Contexte : aucune image publique ne convient, et l'audit veut savoir ce qui tourne

Aucun EE officiel ne fait l'affaire. Le minimal n'a pas les collections que vos
playbooks appellent ; les gros embarquent des centaines de mégaoctets dont vous
ne ferez rien et un `ansible-core` que vous ne maîtrisez pas. Pendant ce temps,
l'équipe sécurité pose une question légitime : qu'est-ce qui s'exécute exactement
sur les hôtes d'automatisation ? « Ce vers quoi pointait `:latest` le jour du
build » n'est pas une réponse qu'elle acceptera, et ce n'en est pas une que vous
sauriez reproduire.

Votre mission, depuis le répertoire du projet :

1. Écrire la recette d'un **EE sur mesure**, au schéma courant, basée sur une
   image minimale et construite avec Podman.
2. **Tout épingler** : `ansible-core`, chaque collection, chaque dépendance Python
   à une version exacte, et déclarer les dépendances système nécessaires.
3. Inspecter le fichier de construction généré par le build : savoir ce qui est
   assemblé plutôt que faire confiance à une boîte noire.
4. Tester l'image obtenue, puis la pousser sur un **registre privé** pour que
   l'équipe consomme une version, et non un tag mouvant.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/ee-builder/
