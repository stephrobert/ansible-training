# Contexte : un fichier qui vous appartient, un fichier où vous n'êtes qu'invité

Deux incidents la même semaine, causes opposées. Le premier : un `lineinfile`
écrit sans `regexp` a ajouté son entrée à `/etc/hosts` à chaque passage,
quarante lignes identiques le jour où quelqu'un a regardé. Le second : un
collègue a décidé de gérer `/etc/hosts` avec un template, s'est approprié le
fichier entier, et a effacé les entrées qu'un autre outil y avait
légitimement posées. Aucun des deux modules n'a tort : ils répondent à des
questions différentes. Vous les mettez côte à côte sur `db1.lab`, depuis
**control-node.lab**.

Votre mission :

1. Ajouter une **seule entrée d'hôte** dans `/etc/hosts` sans déranger les
   lignes déjà présentes.
2. Rendre cet ajout idempotent en **matchant** la ligne au lieu d'empiler
   aveuglément : la regexp manquante, c'est tout le premier incident.
3. Générer `/etc/myapp.conf` **intégralement depuis un template**, chaque
   valeur interpolée depuis des variables structurées.
4. Puis énoncer la règle à voix haute : lequel des deux fichiers vous
   appartient, lequel ne fait que vous accueillir, et pourquoi c'est cette
   réponse, et non le goût, qui choisit le module.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/lineinfile-vs-template/
