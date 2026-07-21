# Contexte : durcir le démon SSH du serveur de base de données

Fail2ban signale un flux continu de tentatives de connexion root sur
**db1.lab**, le serveur qui porte les données de production. La sécurité veut
trois fermetures aujourd'hui : plus de root en SSH, un plafond strict sur les
tentatives d'authentification, et une liste explicite des comptes autorisés. Le
piège : une faute de frappe dans `sshd_config` suivie d'un redémarrage du
service, et plus personne n'entre sur une machine qui ne s'atteint qu'en SSH.
Vous travaillez donc depuis **control-node.lab**, et le démon ne redémarre
jamais sur un fichier invalide.

Votre mission :

1. Désactiver le login root SSH sur **db1.lab**, ramener **`MaxAuthTries` à 3**
   en conservant l'indentation existante de la ligne, et ajouter
   **`AllowUsers ansible`** si elle manque.
2. **Valider le fichier avant chaque écriture** : une configuration que `sshd`
   refuse ne doit jamais atteindre le disque.
3. Redémarrer le démon **une seule fois, à la fin, et uniquement si** quelque
   chose a réellement changé.
4. Garantir l'**idempotence stricte** : le second passage doit afficher
   `changed: 0`.

La méthode complète est dans le guide compagnon :
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-lineinfile/
