# Contexte : un seul mot de passe vault, et les stagiaires lisent la production

Tous les secrets du dépôt sont chiffrés avec le même mot de passe vault, et ce
mot de passe est remis à quiconque doit déployer en dev. Autrement dit : le
stagiaire qui a déployé en dev ce matin peut déchiffrer les identifiants de la
base de production, et rien dans l'outillage ne l'en empêcherait ni ne le
consignerait. Les secrets sont chiffrés. Ils ne sont pas cloisonnés, et ce n'est
pas la même chose.

Votre mission, depuis **control-node.lab** :

1. Donner à chaque environnement sa **propre identité vault étiquetée** et son
   propre mot de passe : détenir la clé de dev ne déchiffre que dev.
2. Ranger les secrets par environnement sous `group_vars/`, dev sur **web1.lab**
   et prod sur **db1.lab**, chaque groupe ne portant que ce qui le concerne.
3. Lancer un seul play sur les **deux** environnements et faire déchiffrer par
   Ansible chaque fichier avec la bonne identité, preuve qu'ils ne se mélangent
   jamais.
4. Lire l'en-tête d'un fichier chiffré pour dire à quelle identité il appartient
   sans le déchiffrer, puis établir qui, dans l'équipe, reçoit quel mot de passe.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-id-multiples/
