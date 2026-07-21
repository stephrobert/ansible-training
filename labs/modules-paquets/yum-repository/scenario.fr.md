# Contexte : ouvrir EPEL sous signature, préparer le dépôt local fermé

L'équipe supervision a besoin de `htop` sur **db1.lab**, et les dépôts de
base ne le fournissent pas : il vit dans **EPEL**. La politique de sécurité
est explicite : rien ne s'installe depuis une source non signée, le dépôt
entre donc avec sa clé GPG importée et la vérification de signature active.
Pendant ce temps, l'équipe build prépare un dépôt RPM interne servi depuis
le disque local ; il doit être **déclaré dès maintenant mais rester fermé**
tant que son contenu n'est pas validé, car un dépôt déclaré et activé
s'invite en silence dans chaque futur `dnf update`. Le tout piloté depuis
**control-node.lab**, et rejouable sans le moindre changement au second
passage.

Votre mission :

1. Importer la **clé GPG EPEL** sur **db1.lab**, puis déclarer le dépôt EPEL
   correspondant à la version de la distribution, **activé et vérifié par
   signature**.
2. Installer **`htop`** depuis ce dépôt.
3. Déclarer le dépôt **`local-test`** (`file:///srv/repo/`), **désactivé** :
   le fichier `.repo` existe sur le disque, le dépôt ne sert jamais.
4. Le prouver : le paquet est installé, EPEL apparaît parmi les dépôts
   actifs, `local-test` reste hors de la liste des dépôts activés, et un
   second passage affiche `changed: 0`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-yum-repository/
