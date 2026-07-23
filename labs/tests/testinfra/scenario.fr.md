# Contexte : les assertions YAML ont dépassé les limites du YAML

Votre `verify.yml` est devenu un mur. Vérifier huit paquets impose huit blocs
quasi identiques, chacun avec son `register` et son `assert`. Quand l'un tombe,
le rapport annonce qu'une tâche a échoué, pas quel paquet manque. Le relecteur
réclame en plus la couverture du service, de la socket, du fichier de conf et des
utilisateurs, et le YAML est déjà plus long que le rôle qu'il teste. Les
assertions ne sont pas fausses : elles ont dépassé les limites de leur langage.

Votre mission, depuis le répertoire du projet :

1. Basculer le **verifier** du scénario sur celui en Python, et faire exécuter
   les nouvelles assertions par le cycle à la place des anciennes.
2. Réécrire les vérifications contre l'instance vivante : paquet installé,
   service démarré, socket en écoute, fichier de conf présent, utilisateurs et
   groupes conformes.
3. Replier les cas répétitifs dans un **unique test paramétré** : huit paquets
   coûtent un seul test, et chaque échec nomme son propre cas.
4. Argumenter l'arbitrage : quand le verifier YAML reste le bon choix, et quand
   Python mérite la dépendance qu'il coûte.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-testinfra/
