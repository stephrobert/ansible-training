# Contexte : quatre transformations que personne ne devrait faire à la main

L'intégration que vous branchez a besoin de quatre choses qu'Ansible ne vous
donne pas toutes faites : le préfixe de rôle de la machine, enfoui dans son
FQDN ; un en-tête d'authentification Basic, donc un couple d'identifiants
encodé en base64 ; une liste qui arrive imbriquée depuis l'export d'une autre
équipe ; et une empreinte sha256 pour savoir si une charge utile a réellement
changé. Les quatre se font à la main aujourd'hui, depuis une page de wiki
pleine de commandes à copier-coller, et cette page est fausse.

Vous les faites dans la donnée, sur `db1.lab`, depuis **control-node.lab**.

Votre mission :

1. **Extraire** le préfixe de rôle d'un FQDN avec une regex, ancrée pour
   s'arrêter avant le premier chiffre.
2. **Encoder** le couple d'identifiants en base64, en restant lucide sur ce que
   c'est : de l'encodage, jamais du chiffrement.
3. **Aplatir** la liste imbriquée, et vérifier jusqu'à quelle profondeur le
   filtre descend avant de renoncer.
4. Produire une empreinte **sha256** d'une chaîne, puis écrire les quatre
   résultats sur db1.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/filtres-jinja/
