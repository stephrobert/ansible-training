# Contexte : viser les bons hôtes sans réécrire le playbook à chaque fois

Le même playbook doit tourner sur un périmètre différent à chaque exécution :
seulement les serveurs web en test, le tier web sauf l'hôte sous investigation,
tout le parc sauf le staging. L'habitude actuelle consiste à éditer la ligne
`hosts:` avant chaque lancement, et l'accident que tout le monde voyait venir
s'est produit la semaine dernière : un périmètre resté en place, et le play est
parti sur tous les serveurs. Le playbook doit cesser de savoir qui il vise.
Cette décision se prend à l'**exécution**, depuis **control-node.lab**.

Votre mission :

1. Écrire un play visant **tous les hôtes**, qui pose un marqueur nommé d'après
   chaque hôte : aucun périmètre figé dans le YAML.
2. Faire réaliser le filtrage à l'**exécution**, pour que le même fichier serve
   les trois périmètres sans la moindre modification.
3. Viser exactement trois cibles : l'**intersection** du tier web et du staging,
   le tier web **moins** un hôte précis, et tout le parc **hors** staging.
4. Prouver la visée : seuls les hôtes attendus portent le marqueur, et les
   autres n'ont jamais été touchés.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/patterns-hotes/
