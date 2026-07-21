# Contexte : personne ne peut relire un mur de chiffré

Chiffrer les fichiers entiers a marché, et les revues sont devenues aveugles.
Votre `host_vars/db1.lab.yml` contient un port d'écoute, une version, un nom
d'utilisateur et exactement un mot de passe. À cause de ce seul mot de passe, tout
le fichier est du chiffré. Un diff dessus annonce qu'un bloc a changé. Les
relecteurs approuvent sans savoir si quelqu'un a bougé un port ou remplacé un
identifiant. Chiffrer le fichier a protégé le secret et tué la revue du même coup.

Votre mission, depuis **control-node.lab** :

1. Dans `host_vars/db1.lab.yml`, garder les valeurs non sensibles **lisibles** et
   ne chiffrer que le mot de passe, sous forme d'une valeur isolée au sein d'un
   YAML par ailleurs en clair.
2. Faire récupérer cette valeur par Ansible de façon transparente au runtime, sans
   étape supplémentaire pour l'appelant.
3. Prouver sur **db1.lab** que les deux natures de variables arrivent exploitables
   côte à côte : le nom d'utilisateur en clair tel qu'écrit, et le mot de passe
   déchiffré.
4. Trancher la règle pour l'équipe : quand la valeur isolée s'impose, et quand il
   vaut mieux chiffrer le fichier entier.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/chiffrer-fichier-variable/
