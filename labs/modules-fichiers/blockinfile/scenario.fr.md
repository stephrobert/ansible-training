# Contexte : livrer les alias shell de l'équipe sans casser le profil

L'équipe d'astreinte veut ses raccourcis habituels sur **db1.lab** : lister les
fichiers, voir le statut git, et surtout afficher les ports ouverts pendant un
incident sans chercher les options de `ss`. Un collègue s'y est déjà essayé, en
collant les alias à la main dans un script de profil, puis en les recollant à la
modification suivante : le bloc y figure désormais trois fois. Vous reprenez le
sujet depuis **control-node.lab**, avec un playbook qui possède son bloc et
cesse de le dupliquer.

Votre mission :

1. Créer **`/etc/profile.d/aliases-rhce.sh`** sur **db1.lab** (mode `0644`), le
   fichier n'existe pas encore.
2. Y maintenir les trois alias de l'équipe dans un **bloc unique encadré par vos
   propres marqueurs**, pour que le bloc soit reconnu et remplacé plutôt
   qu'ajouté à la suite.
3. Prouver l'**idempotence** : après un second passage, le marqueur d'ouverture
   ne doit apparaître qu'**une seule fois** dans le fichier.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-blockinfile/
