# Contexte : le token est ici, le serveur en a besoin là-bas

Le token d'API est dans un fichier sur le control node. **db1.lab** ne l'a
jamais vu, et ne devrait jamais en détenir de copie au-delà du fichier de
configuration que vous allez générer. Un collègue a proposé de copier d'abord
le token sur db1 puis de le lire depuis là, ce qui annule tout l'intérêt de le
garder sur une seule machine. Ansible sait lire une donnée locale au moment du
templating et ne pousser que le résultat. C'est à ça que servent les lookups,
et le sens de circulation est toute la leçon.

Vous travaillez depuis **control-node.lab**.

Votre mission :

1. Lire le **token d'API dans un fichier du control node** et le pousser dans
   `/tmp/lookups-challenge.txt` sur `db1.lab`.
2. Y ajouter une valeur prise dans l'**environnement** du control node, et une
   autre prise dans la **sortie d'une commande** exécutée localement.
3. Vous convaincre du sens : les trois valeurs décrivent votre control node,
   pas db1, alors même que le fichier atterrit sur db1.
4. Retenir qu'un lookup de fichier se résout **relativement au playbook**, et
   non à votre shell, et savoir quand `query` doit remplacer `lookup`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/lookups/
