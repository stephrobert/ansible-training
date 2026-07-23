# Contexte : la donnée arrive sale, la config doit sortir propre

Les valeurs qui alimentent vos configurations viennent de trois sources et
aucune n'est d'accord avec les autres. Un champ arrive rembourré d'espaces et
hurlé en majuscules. Deux listes de paquets se recouvrent et doivent n'en
faire qu'une. Le catalogue de services mélange prod et staging. Une config de
base a besoin d'une surcharge TLS empilée par-dessus. Et une variable est
parfois tout simplement absente, ce qui ne vous prévient pas : ça tue le
templating au milieu du run. Vous nettoyez tout ça **dans la donnée**, sur
`db1.lab`, depuis **control-node.lab**.

Votre mission :

1. Normaliser une chaîne sale, puis fusionner deux listes de paquets en un
   ensemble unique, dédoublonné et trié.
2. Extraire les services de **production** d'une liste de dicts et n'en garder
   que les noms.
3. Fusionner une config de base avec ses surcharges, et comprendre ce qu'un
   merge plat fait aux clés qui se trouvent en dessous.
4. Faire qu'une variable absente **retombe** sur une valeur de repli au lieu
   d'emporter le run, puis écrire les six résultats sur db1.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/filtres-jinja-essentiels/
