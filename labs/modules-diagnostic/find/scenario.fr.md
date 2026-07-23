# Contexte : nettoyer les logs obèses sans supprimer les utiles

Une application de **db1.lab** déverse ses logs dans `/tmp` depuis des semaines,
et certains ont assez grossi pour menacer la partition. La règle retenue par
l'équipe est simple : au-delà d'une certaine taille, le log part ; en dessous, il
reste, parce que les petits sont justement ceux que l'on lit pour déboguer.
Personne ne veut d'un `rm` récité de mémoire à 2 h du matin sur une machine de
production. Vous pilotez le nettoyage depuis **control-node.lab**, et c'est
Ansible qui décide de ce qui part.

Votre mission :

1. Mettre en place le répertoire de travail et ses fichiers de log sur
   **db1.lab** : le terrain sur lequel ce nettoyage s'exécutera.
2. **Rechercher** dans ce répertoire les fichiers `.log` de **plus de 5 Mo**, en
   laissant le module de recherche faire le filtrage plutôt qu'une ligne de
   shell.
3. **Supprimer les seuls fichiers trouvés**, en itérant sur le résultat de la
   recherche : ce qui n'est pas dans la liste n'est pas touché.
4. Prouver le résultat : les petits logs survivent, les gros ont disparu.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-find/
