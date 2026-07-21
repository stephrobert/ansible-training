# Contexte : le mot-clé qui cache vos pannes

Quelqu'un a saupoudré le playbook d'`ignore_errors: true` jusqu'à ce qu'il
cesse d'être rouge. Il est vert, maintenant. Il ment aussi : une migration de
base ratée défile en un discret « ...ignoring », et le play se termine en
succès. Le mot-clé n'est pas diabolique : il a deux ou trois usages honnêtes,
comme un nettoyage qui doit tolérer un service déjà absent. C'est le réflexe
qui pose problème, et le seul remède est de voir précisément ce qu'il fait et
ce qu'il ne fait pas. Vous le mesurez sur `db1.lab`, depuis
**control-node.lab**.

Votre mission :

1. Tenter d'arrêter un service qui n'existe pas sur `db1.lab` : un échec
   garanti, et légitime dans un nettoyage.
2. Ignorer cette erreur explicitement, en plaçant le mot-clé là où il vit : il
   qualifie la tâche, ce n'est pas un paramètre du module.
3. Prouver que le play a continué : la tâche suivante s'exécute, laisse son
   marqueur, et le récapitulatif affiche `failed=0` malgré l'échec.
4. Puis plaider contre vous-même : nommer ce que `failed_when` ou
   `block`/`rescue` vous auraient apporté ici, et qu'un ignore ne donnera
   jamais.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/ignore-errors/
