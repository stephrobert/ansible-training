# Contexte : le rôle qui s'est exécuté alors qu'on lui avait dit non

Un collègue a protégé le rôle `webserver` par un `when:` et un feature flag, et
le rôle s'est quand même déployé sur un hôte qui devait rester intact. La
condition était là, en toutes lettres, et elle a été ignorée. Le bug n'est pas
dans le `when:`, il est dans la façon d'appeler le rôle : deux des trois formes
d'invocation se résolvent au parsing, une seule évalue les conditions au runtime.

Votre mission, depuis le répertoire du projet, contre **db1.lab** :

1. Déployer le rôle `webserver` par la forme standard, au niveau du play, à
   l'écoute sur le port 8080 : paquet, service, page, tout doit se prouver sur
   la cible.
2. **Importer** statiquement l'entry point de trace du rôle, gardé par un
   feature flag éteint, et montrer les deux visages du « statique » : le
   fichier de trace ne doit PAS apparaître, mais les variables par défaut du
   rôle doivent être visibles dans le play, parce que le rôle a de toute façon
   été chargé au parsing.
3. **Inclure** dynamiquement le même entry point, sous une condition qui
   n'existe qu'au runtime (l'état réel du service nginx), et montrer l'image
   miroir : le fichier de trace apparaît, mais les variables du rôle restent
   privées.
4. Formuler la règle que vous donneriez à l'équipe : quelle forme pour un rôle
   systématique, laquelle pour un rôle piloté par tag, laquelle pour un flag
   décidé à l'exécution.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/consommer-role/
