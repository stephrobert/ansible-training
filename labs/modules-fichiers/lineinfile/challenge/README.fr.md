# Durcir le démon SSH du serveur de base de données

## La situation

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
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-lineinfile/

## Challenge `lineinfile:`

### Énoncé

Sur **db1.lab**, écrivez un playbook **`solution.yml`** qui :

1. **Désactive** le login root SSH (`PermitRootLogin no`).
2. Réduit **MaxAuthTries** à `3` (en gardant l'indentation existante via `backrefs`).
3. Ajoute la ligne **`AllowUsers ansible`** si absente.
4. **Valide** chaque modif avec `sshd -t -f %s` avant écriture.
5. Notifie un **handler** `Restart sshd` qui ne se déclenche qu'à la fin si
   au moins une des 3 tâches a `changed`.

> 🎯 **Pas de squelette ici, volontairement.** À ce stade, vous avez écrit
> assez de playbooks pour partir d'un fichier vide, et c'est exactement ce
> que demande l'EX294 : l'examen ne fournit aucun canevas. Les indices
> ci-dessous ciblent les pièges de ce module, pas la syntaxe YAML.

### Critères de réussite

- Premier run : `changed: 3` ou plus selon l'état initial.
- Deuxième run : **`changed: 0`** (idempotence stricte).
- `sshd -T | grep -E "PermitRootLogin|MaxAuthTries|AllowUsers"` retourne les 3 lignes attendues.
- `sshd -t` ne renvoie **aucune** erreur.

### 🧩 Bloqué ?

```bash
dsoxlab hint modules-fichiers-lineinfile
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.
