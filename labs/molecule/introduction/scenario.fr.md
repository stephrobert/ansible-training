# Contexte : « ça marche chez moi » n'est pas un rapport de test

Le rôle `webserver` passe sur votre poste et casse sur celui de votre collègue.
Chaque revue se termine pareil : quelqu'un affirme que le rôle est bon, personne
ne peut le prouver, et la seule façon de vérifier consiste à brûler une VM pour
regarder le résultat à l'œil. Avant d'automatiser quoi que ce soit, l'équipe a
besoin d'un harnais de test lisible et fiable, et d'un vocabulaire commun sur ce
que « testé » veut dire.

Votre mission, depuis le répertoire du projet :

1. Ouvrir le scénario livré dans `molecule/default/` et rendre compte de chacun
   de ses trois fichiers : qui crée l'instance, qui applique le rôle, qui juge
   le résultat.
2. Identifier le **driver** (sur quoi tourne l'instance), les **plateformes**
   (quelles instances sont créées) et le **verifier** (qui prononce le verdict).
3. Dérouler le cycle complet, de la création à la destruction, et situer l'étape
   d'**idempotence** : ce qu'elle rejoue, et ce qu'un échec à ce stade signifie.
4. Confirmer que le scénario est conforme au standard, et pas juste présent.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tdd-molecule-introduction/
