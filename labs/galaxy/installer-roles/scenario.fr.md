# Contexte : le même projet, deux machines, deux résultats

Le déploiement marchait en juillet et échoue aujourd'hui, sur le même commit.
Rien n'a bougé dans le dépôt : un rôle amont a publié une nouvelle version majeure
cette nuit, et le projet l'installe sans épinglage, donc chaque machine tire ce
qui est le plus récent au moment où elle tourne. Votre poste, le runner de CI et
le collègue arrivé la semaine dernière exécutent trois bases de code différentes
depuis des checkouts Git identiques.

Votre mission, depuis le répertoire du projet :

1. Déclarer **toutes** les dépendances du projet dans un manifeste unique : rôles
   Galaxy, rôles tirés directement de **Git**, et collections, pour que plus rien
   ne s'installe par tradition orale.
2. Les **épingler** toutes, en choisissant l'épinglage adapté à chaque cas : une
   version exacte là où la surprise est interdite, une plage bornée ailleurs.
3. Distinguer les deux chemins d'installation : rôles et collections
   n'atterrissent pas au même endroit, et aucun des deux n'est versionné par le
   dépôt.
4. **Vendoriser** dans le projet le seul rôle que vous ne pouvez pas perdre, et
   justifier pourquoi celui-là et pas les autres.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/installer-roles-galaxy/
