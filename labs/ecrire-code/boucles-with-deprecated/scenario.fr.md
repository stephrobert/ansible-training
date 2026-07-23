# Contexte : le playbook dont vous héritez a été écrit en 2016

Vous reprenez un dépôt auquel personne n'a touché depuis des années. Il
marche. Il fait aussi échouer la barrière de lint de la CI dès son premier
fichier : du `with_items` partout, un `with_dict` sur la table des ports, un
`with_subelements` que personne n'ose lire à voix haute. La syntaxe est
dépréciée, pas cassée, et c'est exactement pour ça qu'elle est encore là. Elle
continuera de marcher jusqu'à la version qui la supprime, et cette version
n'est pas loin.

Vous modernisez les itérations sur `db1.lab`, depuis **control-node.lab**.

Votre mission :

1. Réécrire l'itération sur liste simple avec **`loop:`**, le remplacement
   moderne au un pour un.
2. Migrer la table des ports : un dict ne s'itère **pas** directement. Le
   convertir en liste de paires et atteindre la clé comme la valeur.
3. En profiter pour garder la console lisible : étiqueter chaque itération par
   ce qu'elle fait réellement.
4. Atteindre zéro dépréciation sur `ansible-lint`, et découvrir laquelle de ces
   réécritures le linter peut faire à votre place.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-with-deprecated/
