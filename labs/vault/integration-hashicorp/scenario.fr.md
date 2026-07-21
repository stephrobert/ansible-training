# Contexte : une administratrice est partie, et personne ne sait ce qu'elle pouvait lire

La procédure de départ posait une question simple, et l'équipe n'a pas su
répondre : à quels secrets avait-elle accès, et lesquels sont désormais
compromis ? Tous les secrets du dépôt sont chiffrés avec un mot de passe vault
qu'elle détenait, donc la réponse est « tous », et le remède consiste à tout faire
tourner à la main. Aucune piste d'audit, aucune rotation, aucune expiration.
Ansible Vault protège un fichier. Il ne gère pas la vie d'un secret.

Votre mission, depuis le répertoire du projet :

1. Monter un **serveur de secrets local** (HashiCorp Vault ou son fork open
   source) et y stocker les identifiants de l'application, pour que le secret vive
   dans un système capable de le journaliser, le faire tourner et l'expirer.
2. Faire **lire** ce secret au runtime par un playbook via la collection dédiée,
   avec le point de montage explicite et **aucune valeur secrète écrite dans le
   YAML**, jamais.
3. Garder le montage interchangeable entre les deux implémentations : l'API est la
   même, et la question de licence ne doit pas réécrire vos playbooks.
4. Comparer les modes d'authentification (token, AppRole, JWT) et dire lequel
   revient à un humain, lequel à la CI, et pourquoi le token de dev n'est ni l'un
   ni l'autre.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-hashicorp-vault/
