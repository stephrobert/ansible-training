# Contexte : des tests écrits après le code sont toujours d'accord avec le code

Les rôles de l'équipe sont tous testés, et les tests n'attrapent jamais rien.
L'historique Git dit pourquoi : les tâches sont écrites d'abord, les assertions
ensuite, et elles finissent par décrire ce que le code fait plutôt que ce qu'on
avait demandé. Vous démarrez un nouveau rôle `users`, et cette fois l'ordre est
inversé : on n'écrit rien tant qu'un test ne le réclame pas.

Votre mission, depuis le répertoire du projet :

1. Écrire les **assertions d'abord**, sur un rôle dont les tâches n'existent pas
   encore, et lancer le cycle pour les voir échouer. Un test qui n'a jamais
   échoué ne prouve rien.
2. Déclarer le contrat d'entrée du rôle avant son code : la forme et le type de
   la liste d'utilisateurs à créer, pour qu'un appel fautif soit rejeté d'entrée.
3. Écrire alors le **minimum** de tâches qui font passer les assertions au vert,
   en bouclant sur les utilisateurs demandés plutôt qu'en figeant le moindre nom.
4. Refactorer une fois au vert, en utilisant la suite comme filet : elle doit
   rester verte pendant la réécriture, sinon elle ne vous protégeait pas.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-tdd-cycle/
