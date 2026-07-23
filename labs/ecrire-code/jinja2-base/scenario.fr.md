# Contexte : une bannière de connexion qui ment sur la machine

Chaque hôte vous accueille avec une bannière tapée à la main il y a des
années. La moitié annonce encore un service décommissionné depuis deux
réorganisations, l'une vous souhaite la bienvenue sur un hostname qui n'existe
plus, et toutes sont truffées de lignes vides parasites laissées par une
précédente tentative de génération. L'exploitation veut une seule bannière :
générée, juste sur chaque hôte, et lisible.

Vous commencez par **db1.lab**, depuis **control-node.lab**.

Votre mission :

1. Générer `/etc/motd-challenge` depuis un **template Jinja2**, l'hôte se
   nommant lui-même depuis l'inventaire plutôt que par une chaîne en dur.
2. N'afficher la ligne de rôle **que si** l'hôte porte réellement ce rôle : une
   condition dans le template, pas deux templates côte à côte.
3. Lister les services de l'hôte avec une **boucle** pilotée par une variable,
   un par ligne.
4. Supprimer les lignes vides parasites avec le **whitespace control** : c'est
   toute la différence entre une bannière générée et une bannière qui a l'air
   générée.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/jinja2-base/
