# Contexte : trois secrets qui ne doivent jamais atterrir dans un log

L'application de **db1.lab** a besoin d'un fichier de configuration portant un
mot de passe de base, un secret JWT et un token Redis. La dernière fois que ça
a été fait à la main, les trois valeurs se sont retrouvées en clair dans
l'historique Git et dans la sortie console de la CI. L'audit vous a laissé une
règle : les secrets vivent chiffrés dans le dépôt, ils ne sont déchiffrés
qu'au runtime, et ils n'apparaissent dans **aucune** sortie Ansible.

Depuis **control-node.lab**, vous construisez cette chaîne de bout en bout.

Votre mission :

1. Garder le mot de passe vault dans un fichier en `0600`, gitignoré, et nulle
   part ailleurs.
2. Chiffrer les trois secrets dans un **fichier YAML Vault**, puis vérifier sur
   le disque qu'il commence bien par l'en-tête `$ANSIBLE_VAULT`.
3. Le consommer via **`vars_files`** pour générer `/tmp/db1-app.conf` sur
   `db1.lab`, propriétaire `root`, mode `0600`.
4. Museler la tâche qui les manipule pour que les valeurs ne remontent jamais
   en console, en sachant que ce mot-clé appartient à la tâche et non au
   module.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premiers-pas-ansible-vault/
