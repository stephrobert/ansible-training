# Contexte : installer l'outillage EPEL sur db1 sans embarquer le kernel

Le DBA veut deux outils de diagnostic sur **db1.lab** pour traquer une
saturation disque : un visualiseur de processus en direct et un explorateur
d'occupation de répertoires. Aucun des deux n'existe dans les dépôts de base
d'AlmaLinux : ils vivent dans EPEL. Le dernier collègue qui a activé un dépôt
tiers a aussi laissé un metapaquet tirer un kernel neuf, et la base de données a
redémarré sur un noyau non testé. Cela ne se reproduira pas. Vous travaillez
depuis **control-node.lab**, et la transaction reste sous contrôle.

Votre mission :

1. Ajouter le dépôt **EPEL** sur **db1.lab** via son paquet officiel de
   release, plutôt qu'en écrivant un fichier `.repo` à la main.
2. Installer les deux outils de diagnostic en **activant EPEL explicitement**
   pour cette transaction et en **rafraîchissant le cache de metadata** au
   préalable.
3. **Exclure tous les paquets kernel** de la transaction : aucune dépendance ne
   doit faire monter le noyau d'une base de production par effet de bord.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-dnf-options/
