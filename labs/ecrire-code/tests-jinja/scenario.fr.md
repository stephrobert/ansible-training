# Contexte : le template qui a planté sur une chaîne prise pour une liste

Le générateur a marché pendant un an. Puis quelqu'un a passé une valeur unique
là où le template attendait une liste. Jinja a itéré dessus sans broncher,
caractère par caractère, et a produit une config avec une ligne par lettre.
Personne ne l'a vu jusqu'à ce que le service refuse de démarrer. Un autre
jour, une variable optionnelle était simplement absente et le run est mort en
plein rendu. Un template qui fait confiance à son entrée est un template qui
attend le jour où l'entrée changera. Vous le faites **vérifier avant d'agir**,
sur `db1.lab`, depuis **control-node.lab**.

Votre mission :

1. Écrire dans `/tmp/tests-jinja.txt` des lignes conditionnelles qui ne
   s'affichent que si leur test passe réellement.
2. Tester l'**existence** et tester le **type** : une variable définie, une
   valeur qui est vraiment un dict, une valeur qui est vraiment une liste.
3. Tester aussi le cas négatif : une variable optionnelle jamais définie doit
   être **détectée comme non définie**, pas faire planter le rendu.
4. Ne pas mélanger les deux syntaxes : un filtre se met après `|`, un test
   après `is`. Puis garder la sortie propre avec le whitespace control.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/tests-jinja/
