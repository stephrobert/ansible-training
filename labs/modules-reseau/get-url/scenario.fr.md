# Contexte : sortir les appels curl cachés dans le playbook de provisioning

Le playbook qui provisionne **db1.lab** télécharge encore ses fichiers de
référence avec `command: curl`, et cela se voit. Chaque passage annonce
`changed`, parce qu'une commande shell n'a aucune idée de la présence du fichier,
et la chaîne d'intégration ne distingue plus un vrai changement du bruit de fond.
Rien ne vérifie non plus ce qui atterrit sur le disque : ce que le miroir sert
est écrit tel quel, corrompu ou non. L'un des deux fichiers ne doit jamais être
écrasé une fois en place : c'est la référence que l'équipe amende localement, et
un nouveau téléchargement efface ces modifications en silence. Celui-là n'est
d'ailleurs plus en libre accès : le dépôt interne le sert désormais depuis une
zone protégée. Vous nettoyez depuis **control-node.lab**, sans laisser une seule
commande shell.

Votre mission :

1. Télécharger les deux documents de référence sur **db1.lab** dans `/opt/`,
   mode `0644`, avec le **module Ansible dédié** : pas de `curl`, pas de `wget`.
2. **Vérifier l'intégrité** du document public à partir du **fichier de sommes
   sha256 que le dépôt publie à côté de lui**, plutôt que de faire confiance aux
   octets qui arrivent. Sans figer d'empreinte dans le playbook.
3. **Authentifier** la requête du second document, que le dépôt sert depuis une
   zone protégée.
4. Protéger ce second fichier pour qu'**une copie déjà présente ne soit jamais
   retéléchargée**, quoi que serve désormais la source amont.
5. Prouver l'**idempotence** : un second passage ne télécharge rien et n'annonce
   aucun changement.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-get-url/
