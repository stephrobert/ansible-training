# Contexte : le tableur partagé des mots de passe doit disparaître

Vos playbooks tirent leurs secrets d'infrastructure d'un vrai serveur dédié. Les
humains, non. Les comptes SaaS, les clés d'API tierces, les passphrases de
certificats et le login d'administration que tout le monde utilise vivent dans un
tableur sur un partage réseau, parce que l'équipe a besoin de les lire avec ses
yeux, pas seulement depuis un playbook. Ces secrets méritent un toit qui serve les
deux : une interface web qu'un humain utilisera vraiment, et une interface
qu'Ansible sait interroger.

Votre mission, depuis le répertoire du projet :

1. Monter une instance **Passbolt locale** avec sa base de données, puis créer le
   compte d'administration et la **clé OpenPGP** qui vous identifie auprès d'elle.
2. Faire récupérer un secret par un playbook via la collection dédiée, en vous
   authentifiant par votre clé privée et sa passphrase, avec **aucune valeur
   secrète en dur** dans le YAML.
3. Museler les tâches sensibles pour que le secret n'apparaisse ni dans la sortie
   ni dans les journaux, quelle que soit la verbosité.
4. Positionner l'outil face à un serveur de type HashiCorp : son modèle
   d'identité, c'est une clé par humain, pas un token par machine. Dire quels
   secrets vont où.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-passbolt/
