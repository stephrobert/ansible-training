# Contexte : le rôle embarque ses secrets, et personne ne peut les changer

Le rôle `secured_app` voyage avec les identifiants dont il a besoin, chiffrés à
l'intérieur du rôle. Cela règle la distribution et crée un autre problème : une
équipe qui veut son propre mot de passe de base doit déchiffrer les entrailles du
rôle, les éditer, puis les rechiffrer. Alors elle forke. Trois forks plus tard, un
correctif de sécurité doit être appliqué quatre fois. Les secrets du rôle le
regardent ; les valeurs qu'un appelant utilise, non.

Votre mission, depuis **control-node.lab** :

1. Garder les secrets du rôle **chiffrés dans le rôle**, dans le fichier de
   variables que l'appelant n'est pas censé toucher.
2. Les exposer via des **variables publiques surchargeables** qui pointent vers
   les variables chiffrées : l'appelant voit un réglage, jamais du chiffré.
3. Prouver sur **db1.lab** que l'indirection fonctionne dans les deux sens : une
   valeur par défaut intacte résout bien le secret déchiffré, et une valeur
   surchargée depuis le play l'emporte.
4. Expliquer la précédence sur laquelle vous venez de vous appuyer, et pourquoi la
   variable publique devait vivre là où elle est pour que la surcharge soit
   seulement possible.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-dans-roles/
