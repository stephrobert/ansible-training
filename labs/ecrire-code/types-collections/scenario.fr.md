# Contexte : la staging qui fuit dans la config de production

Le catalogue de services tient dans une seule liste : nom, port, tier. Quatre
entrées aujourd'hui, quarante au prochain trimestre. Le fichier qui alimente
la supervision de production est maintenu à la main depuis cette liste, et la
dernière mise à jour y a discrètement glissé un port de staging. Personne ne
l'a vu jusqu'à ce que la supervision réveille quelqu'un à 3 heures du matin
pour une base de dev. Le catalogue va bien : c'est la recopie manuelle qui
échoue. Depuis **control-node.lab**, vous générez la vue production depuis le
catalogue lui-même.

Votre mission :

1. Déclarer le catalogue sur `db1.lab` sous forme de **liste de dicts**, chaque
   entrée portant son nom, son port et son tier.
2. Générer `/tmp/services-production.txt` ne contenant **que** le tier
   `production`, un `<nom>:<port>` par ligne.
3. Filtrer **dans la donnée**, pas à la main : les entrées staging et dev ne
   doivent jamais atteindre le fichier, quel que soit l'ordre du catalogue.
4. Vérifier que le résultat tient en exactement les deux lignes attendues, et
   rien d'autre, en accédant aux champs imbriqués pour composer chaque ligne.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/types-collections/
