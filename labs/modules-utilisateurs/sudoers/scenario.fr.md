# Contexte : refaire les droits sudo après l'ère du « tout le monde est root »

L'audit de **db1.lab** a trouvé ce qui arrive quand sudo pousse tout seul :
quelques personnes disposent du root complet, sans mot de passe, et personne ne
se souvient de l'avoir accordé. Il reste trois besoins légitimes, et trois
seulement. Alice administre la machine, mais doit ressaisir son mot de passe
pour qu'un terminal volé ne soit pas un shell root gratuit. L'équipe ops
automatise et ne peut pas s'arrêter sur une invite. Et Alice doit lancer le
script de déploiement **en tant que compte de service**, sans devenir root. Une
faute de frappe dans un fichier sudo verrouille toute l'équipe dehors.

Votre mission :

1. Depuis **control-node.lab**, poser les prérequis sur **db1.lab** : les
   comptes, le groupe ops et son appartenance.
2. Accorder à Alice le **sudo complet avec mot de passe exigé**, et au groupe
   ops le **sudo complet sans mot de passe** : attention au défaut du module, il
   ne penche pas du côté que l'on espère.
3. Autoriser Alice à lancer **le seul script de déploiement**, et **en tant que
   compte deploy**, pas en root.
4. Faire atterrir chaque règle dans **son propre fichier sous
   `/etc/sudoers.d/`**, validé syntaxiquement avant toute écriture sur le disque.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-sudoers/
