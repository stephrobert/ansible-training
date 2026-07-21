# Contexte : trois comptes demandés, un déjà révoqué

Les RH ont envoyé la liste : trois comptes à créer sur **db1.lab**, chacun
avec son shell. Entre la demande et aujourd'hui, l'un d'eux a été révoqué : la
personne n'a jamais rejoint l'entreprise. La liste porte toujours les trois,
avec un drapeau qui dit lesquels sont actifs, parce que cette liste est la
source de vérité et que personne n'a le droit de la tailler à la main. Votre
playbook doit lire le drapeau, pas la longueur.

Vous l'écrivez depuis **control-node.lab**.

Votre mission :

1. Itérer sur la liste des comptes et ne créer **que ceux marqués actifs**,
   chacun avec le shell qu'il réclame.
2. Garantir que le compte révoqué **n'existe pas** sur l'hôte, même si un run
   antérieur l'avait créé avant la révocation.
3. Garder la console lisible : quarante comptes affichés en dicts bruts, c'est
   un mur de bruit. **Étiquetez** chaque itération par son nom.
4. Écrire un récapitulatif listant les comptes actifs, par ordre alphabétique
   et séparés par des virgules, dérivé de cette même liste plutôt que ressaisi.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-loop/
