# 09 – Sécurisation des données sensibles avec Ansible Vault

Bienvenue dans le septième TP de la formation Ansible ! Ce TP vous apprendra à
**crypter et déchiffrer des données sensibles** avec **Ansible Vault**, et à les
utiliser dans vos playbooks de manière sécurisée.

---

## 🧠 Lecture recommandée

Avant de commencer, je vous recommande de lire cette section du guide : 🔗
[Ansible Vault – Sécuriser les données
sensibles](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/vault/)

Vous y apprendrez :

* Comment créer et déchiffrer un fichier chiffré avec `ansible-vault`
* Comment intégrer des données Vault dans un playbook
* Comment utiliser la commande `--ask-vault-pass` pour déchiffrer à la volée
* Comment utiliser des mots de passe de Vault via un fichier

---

## 🎯 Objectifs du TP

1. Chiffrer un fichier contenant des données sensibles
2. Utiliser ce fichier dans un playbook Ansible
3. Déchiffrer le fichier automatiquement avec un mot de passe ou un fichier de
   passe
4. Utiliser Ansible Vault avec des inventaires et des group_vars

---

## ⚙️ Étapes du TP

### Étape 0 : Prérequis

Assurez-vous que vous avez une machine cible (locale ou distante). Pour
simplifier, vous pouvez utiliser un conteneur Incus ou une machine Ubuntu.

```bash
incus launch images:ubuntu/24.04/cloud web01 --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:ubuntu/24.04/cloud db01 --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"

incus alias add login 'exec @ARGS@ -- su -l admin'
```

---

### Étape 1 : Créer un fichier de données sensibles avec Ansible Vault

Créez un fichier `group_vars/all` et **chiffrez-le** avec la commande
suivante :

```bash
ansible-vault create group_vars/all
```

Lors de la création, vous serez invité à saisir un **mot de passe Vault**
(retenez-le ou créez un fichier `vault_password.txt` avec le mot de passe
dedans, par exemple).

Dans le fichier, ajoutez des données sensibles comme :

```yaml
database_password: "monmotdepasse123!"
```

---

### Étape 2 : Créer un playbook qui utilise ces données

Créez un fichier `install_service.yml` avec le contenu suivant :

```yaml
---
- name: TP Vault – Installer un service avec des données sensibles
  hosts: all
  tasks:

    - name: Afficher le mot de passe de la base de données (sécurisé)
      debug:
        msg: "Le mot de passe de la base de données est : {{ database_password }}"
```

---

### Étape 3 : Exécuter le playbook avec le mot de passe Vault

Pour déchiffrer le fichier, exécutez le playbook avec l’option
`--ask-vault-pass` :

```bash
ansible-playbook --ask-vault-pass install_service.yml
```

---

### Étape 4 : Utiliser un fichier de mot de passe

Créez un fichier `vault_password.txt` avec le mot de passe Vault à l’intérieur.

Puis exécutez le playbook avec l’option `--vault-password-file` :

```bash
ansible-playbook --vault-password-file vault_password.txt install_service.yml
```

---

### Étape 5 : Nettoyage

```bash
incus delete myvaulthost --force
```

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : Vous devrez
créer un playbook qui déchiffre automatiquement un fichier Vault contenant une
clé SSH, et l’utilise pour copier un fichier sur la machine cible. Validez cette
logique avec un test `pytest` + `testinfra`.

---

## ✅ Compétences acquises

* Création et utilisation de fichiers chiffrés avec Ansible Vault
* Déchiffrement automatique via `--ask-vault-pass` ou `--vault-password-file`
* Intégration de données Vault dans des playbooks et des inventaires
* Gestion de données sensibles de manière sécurisée

