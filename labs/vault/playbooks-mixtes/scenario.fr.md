# Contexte : il faut le mot de passe vault juste pour lire un numéro de port

L'accueil d'un nouveau a buté cette semaine. Une collègue voulait savoir sur quel
port écoutent les serveurs web. Cette valeur est publique, sans enjeu, et enfermée
dans un fichier `group_vars` chiffré, à côté d'un token d'administration : lui
répondre imposait de lui confier le mot de passe vault. La configuration de
l'équipe et ses secrets vivent dans le même fichier, et c'est le secret qui dicte
les règles d'accès aux deux.

Votre mission, depuis **control-node.lab** :

1. Couper chaque `group_vars/<groupe>/` en deux : la configuration publique en
   clair, les secrets dans un **fichier chiffré séparé** chargé au même endroit.
2. Adopter une convention de nommage qui rende une variable sensible
   reconnaissable au premier coup d'œil, sans rien ouvrir.
3. Vérifier qu'Ansible fusionne les deux fichiers de façon transparente au
   runtime : prouver sur **web1.lab** que valeurs publiques et secrets
   déchiffrés, venus du groupe `all` comme du groupe web, atterrissent tous dans
   le même play.
4. Constater le gain : `main.yml` reste lisible, et ses diffs restent relisibles.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/playbooks-mixtes/
