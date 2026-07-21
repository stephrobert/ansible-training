# Contexte : la valeur par défaut qui est partie en production

Le playbook de `db1.lab` porte ses valeurs dans le fichier : nom du service,
port, moteur de base, limite de connexions. Vendredi dernier, quelqu'un a
modifié ce fichier pour pointer un run vers la production, l'a lancé, et a
oublié de revenir en arrière. Le collègue suivant a récupéré le dépôt et a
poussé des réglages de production sur un hôte de test. Les valeurs ne sont pas
le problème : les figer à un seul endroit, et **modifier cet endroit pour
changer un run**, si. Vous restructurez ça depuis **control-node.lab**.

Votre mission :

1. Séparer les sources : garder l'identité du service dans les **`vars:`** du
   play, déplacer les réglages de base dans un fichier externe chargé par
   **`vars_files:`**.
2. Lancer une fois sans rien passer en ligne de commande : chaque variable doit
   prendre la valeur venant de sa propre source.
3. En surcharger deux au runtime avec **`--extra-vars`**, sans toucher au
   moindre fichier.
4. Écrire les valeurs résolues sur `db1.lab` et les relire : seules les deux
   surchargées ont bougé. Puis dire pourquoi, si les deux sources portaient la
   même variable, c'est `vars_files:` (niveau 14) qui l'emporterait sur les
   `vars:` du play (niveau 12), et non l'inverse.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/variables-base/
