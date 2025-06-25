# 08 – Écriture de rôles Ansible

Bienvenue dans ce TP consacré à l'écriture de **rôles Ansible**. Ce TP contient
plusieurs Étapes conçus pour vous faire pratiquer la création de rôles
réutilisables et bien structurés.

---

## 📚 Lecture recommandée

Avant de commencer, lisez le guide suivant : [Comment écrire un rôle
Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/)

Vous y apprendrez :

* La structure standard d'un rôle (`tasks`, `handlers`, `defaults`, etc.)
* L'utilisation des variables et des handlers dans un rôle
* Comment rendre un rôle réutilisable et idempotent
* Comment initialiser un rôle avec `ansible-galaxy init`

---

## 🧪 Objectifs du TP

* Créer un rôle avec la commande `ansible-galaxy init`
* Utiliser `notify` et `handlers` pour la gestion des services
* Gérer des variables via `defaults` et `vars`
* Structurer un rôle réutilisable et personnalisable

---

## 📝 Étapes guidées

### Étape 0 : Préparation de l’environnement

Lancez quelques conteneurs :

```bash
incus launch images:debian/12/cloud server1  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:almalinux/9/cloud server2  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

### ✏️ Étape 1 : Créer le rôle sshd

1. Placez-vous dans le répertoire `06-Roles` :

```bash
cd 06-Roles
```

2. Exécutez dans un terminal :

```bash
ansible-galaxy init roles/sshd
```

3. Dans `roles/sshd/tasks/main.yml`, écrivez le contenu suivant :

```yaml
---
- name: Installer le serveur SSH
  ansible.builtin.package:
    name: openssh-server
    state: present

- name: Désactiver la connexion root
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: 'PermitRootLogin no'
    state: present
    backup: true
```

4. Editez le fichier `roles/sshd/handlers/main.yml` avec le contenu suivant :

```yaml
---
- name: Redémarrer ssh
  ansible.builtin.service:
    name: ssh
    state: restarted
```

5. Testez le rôle avec ce playbook `playbook.yml` :

```yaml
---
- name: Test du rôle sshd
  hosts: server1
  become: true
  roles:
    - sshd
```

Lancez avec :

```bash
ansible-playbook playbook.yml
```

Normalement, le serveur SSH devrait être installé et la connexion root
désactivée sur `server1`. Par contre, sur `server2`, vous devriez voir une erreur
car le rôle n'est pas encore adapté pour AlmaLinux. Le nom du service SSH
peut varier selon la distribution, ce qui est normal.

### ✏️ Étape 2 : Ajouter des variables personnalisables

Pour rendre le rôle plus flexible, vous allez ajouter des variables
personnalisables pour le nom du paquet SSH, la configuration de la connexion
root et le nom du service SSH.

1. Modifiez `roles/sshd/defaults/main.yml` :

```yaml
---
sshd_package: openssh-server
permit_root_login: 'no'
sshd_service: ssh
```

2. Adaptez `tasks/main.yml` pour utiliser ces variables :

```yaml
- name: Installer le serveur SSH
  ansible.builtin.package:
    name: "{{ sshd_package }}"
    state: present

- name: Désactiver la connexion root
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: "PermitRootLogin {{ permit_root_login }}"
    state: present
    backup: true
  notify: Redémarrer ssh
```

3. Modifiez le handler pour utiliser la variable `sshd_service` :

```yaml
- name: Redémarrer ssh
  ansible.builtin.service:
    name: "{{ sshd_service }}"
    state: restarted
```

4. Editez le playbook :

```yaml
---
- name: Test du rôle sshd avec surcharge
  hosts: all
  become: true
  roles:
    - role: sshd
      vars:
        permit_root_login: 'prohibit-password'
```

4. Testez le rôle sur les deux machines.

Vous devriez voir que la configuration SSH est appliquée correctement sur les
deux distributions, avec la variable `permit_root_login` modifiée.
Malgré cela, le nom du service SSH reste `ssh` par défaut, ce qui peut poser
problème sur certaines distributions comme AlmaLinux où le service s'appelle
`sshd`.

### ✏️ Étape 3 : Utiliser `include_vars` avec `with_first_found`

Dans cet étape, vous allez faire en sorte que le rôle `sshd` adapte
automatiquement sa configuration selon la distribution utilisée. Vous utiliserez
`include_vars` avec `with_first_found`.

1. Avant la première tâche du fichier `roles/sshd/tasks/main.yml` ajoutez la
   tâche permettant de charger les variables spécifiques à la distribution :

```yaml
---
- name: Inclure les variables spécifiques à la distribution
  ansible.builtin.include_vars: "{{ item }}"
  with_first_found:
    - files:
        - "{{ ansible_distribution | lower }}.yml"
        - "default.yml"
      skip: true
```

1. Créez les fichiers :

```bash
touch roles/sshd/vars/debian.yml
touch roles/sshd/vars/almalinux.yml
touch roles/sshd/vars/default.yml
```

3. Contenu de `debian.yml` :

```yaml
---
sshd_service: ssh
```

4. Contenu de `almalinux.yml` :

```yaml
---
sshd_service: sshd
```

5. Contenu de `default.yml` :

```yaml
---
sshd_service: ssh
```

1. Pour forcer une modification de la configuration SSH, dans le fichier
   `playbook.yml`, remettez la variable `permit_root_login` à `no` :

```yaml

7. Testez le rôle sur les deux machines :

```bash
ansible-playbook playbook.yml
```

Le service devrait normalement être redémarré correctement sur les deux
machines, et la configuration SSH appliquée selon la distribution.

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : Vous devrez
écrire un rôle Ansible permettant de configurer le service **rsyslog**.

---

## 🎯 Compétences acquises

* Création et structuration d’un rôle Ansible avec `ansible-galaxy`
* Utilisation de `handlers` pour redémarrer un service conditionnellement
* Personnalisation du comportement d’un rôle via des variables
* Adaptation automatique selon la distribution grâce à `with_first_found`

Vous êtes maintenant prêt à réutiliser vos rôles dans des playbooks complexes ✨
