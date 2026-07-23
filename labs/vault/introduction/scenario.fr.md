# Contexte : le mot de passe de la base est dans l'historique Git

L'audit de sécurité l'a trouvé ce matin : un `db_secrets.yml` commité en clair il
y a dix-huit mois, toujours lisible par quiconque peut cloner le dépôt. Supprimer
le fichier ne change rien, Git se souvient. Le mot de passe tourne aujourd'hui, et
le nouveau n'ira pas s'écrire dans un YAML en clair. Ce que le dépôt contiendra
désormais, c'est du chiffré, déchiffré au dernier moment sur le nœud de contrôle.

Votre mission, depuis **control-node.lab** :

1. Chiffrer les deux fichiers de secrets dont l'application a besoin, pour que ce
   qui atterrit dans Git soit illisible sans le mot de passe vault, et vérifier
   que le chiffrement est réel en inspectant le fichier.
2. Consulter et modifier un fichier chiffré **sans** laisser traîner de copie
   déchiffrée sur le disque.
3. Faire consommer les **deux** fichiers chiffrés par un playbook en un seul run
   et prouver, sur **db1.lab**, que leurs valeurs sont arrivées intactes, dans un
   fichier lisible du seul root.
4. Traiter la rotation elle-même : changer le mot de passe vault d'un fichier
   existant, et savoir remettre un fichier en clair quand il n'a plus de secret.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/ansible-vault-introduction/
