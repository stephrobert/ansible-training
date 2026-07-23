# Contexte : la moitié du parc à jour, c'est pire que rien

La livraison de config de mardi a atteint **web1.lab**, échoué sur
**web2.lab**, et s'est arrêtée là. C'est le comportement par défaut, et ça
paraît raisonnable jusqu'à ce qu'on regarde le résultat : deux webservers
derrière le même répartiteur de charge, avec deux configurations différentes,
qui donnent deux réponses différentes à la même requête. Le support a passé
une journée à traquer un bug qui n'apparaissait qu'un rafraîchissement sur
deux. Pour ce genre de changement, à moitié appliqué est pire que pas
appliqué. Vous posez la règle au niveau du **play**, depuis
**control-node.lab**.

Votre mission :

1. Écrire un déploiement en deux étapes sur les deux webservers : préparer la
   release, passer un contrôle de santé, puis activer la release. Chaque
   étape laisse un fichier marqueur par hôte, pour que rien ne puisse être
   affirmé sans preuve.
2. Faire échouer le contrôle de santé sur l'hôte désigné par une variable
   `fail_host` (`none` par défaut), pour simuler un incident à la demande
   avec `-e fail_host=web1.lab`.
3. Activer le mot-clé de play qui **arrête tout le play** dès qu'un hôte
   échoue : quand web1 rate son contrôle de santé, web2 ne doit PAS activer
   sa release, alors qu'il n'a lui-même rien raté. C'est cette absence que
   la validation vérifie.
4. Puis le situer : le comparer au comportement par défaut et à
   `max_fail_percentage`, qui tolère un seuil au lieu d'exiger la perfection,
   et déterminer ce qu'il donne combiné à `serial`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/any-errors-fatal/
