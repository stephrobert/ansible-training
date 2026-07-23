# Contexte : vingt minutes à deviner, et un mot de passe dans les logs de la CI

Une tâche échoue sur **db1.lab** avec un message qui ne dit rien d'utile, et le
réflexe de l'équipe consiste à relancer avec tous les `-v` que le clavier peut
tenir. Résultat : des milliers de lignes, et la seule qui comptait enterrée
dedans. Puis quelqu'un a vu le vrai dégât : une tâche qui manipulait un token
avait imprimé ses arguments en entier dans un log que tout le monde peut lire. La
verbosité est un scalpel, et l'équipe s'en sert comme d'un marteau, sur un playbook
à qui personne n'a demandé de se taire.

Votre mission, depuis **control-node.lab** :

1. Accorder le **niveau de verbosité au symptôme** : lequel montre les arguments
   réellement reçus par un module après templating, et lequel parle de la connexion
   SSH et n'a rien à dire sur votre bug.
2. Activer le **profilage des tâches** sur un play de trois tâches mesurables
   contre **db1.lab**, sans toucher aux tâches elles-mêmes, et lire les temps.
3. Rendre la sortie lisible : remplacer le callback du terminal par un que l'œil
   humain peut parcourir en incident, et déposer la preuve du profilage dans un
   fichier sur la cible.
4. Constater ce qu'un **`no_log` manquant** laisse fuiter en verbosité haute, et
   corriger.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/verbosite-vvv/
