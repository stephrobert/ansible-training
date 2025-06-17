# 08 – Utiliser les blocks dans Ansible

Bienvenue dans ce TP consacré à l’utilisation des **blocks** dans Ansible. Les
blocks permettent de regrouper des tâches, appliquer des directives communes
(comme `when`, `become`, ou `tags`), et gérer finement les erreurs avec `rescue`
et `always`.

---

## 📚 Lecture recommandée

Avant de commencer, lisez le guide suivant : [Blocks
Ansible](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/blocks/)

Vous y apprendrez :

* Comment structurer un bloc `block:` avec `rescue:` et `always:`
* À quoi servent les blocks dans une stratégie de gestion des erreurs
* Comment leur appliquer des `when`, `become`, `tags`, etc.

---

## 🧪 Objectifs du TP

* Structurer des tâches dans un `block` logique
* Gérer une erreur simulée avec une clause `rescue`
* Exécuter des actions de nettoyage avec `always`

---

## 📝 Exercices guidés

### Étape 0 : Préparation de l’environnement

Lancez quelques conteneurs incus si nécessaire :

```bash
incus launch images:debian/12/cloud server1  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus launch images:almalinux/9/cloud server2  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
```

### ✏️ Étape 1 : Premier block avec `when` et `become`

1. Créez un fichier `block-sshd.yml` et copiez-y le contenu suivant :

```yaml
---
- name: TP Blocks - Gestion du service SSH
  hosts: all
  tasks:
    - name: Gérer le service SSH sur Debian
      when: ansible_os_family == 'Debian'
      become: true
      tags: ssh
      block:
        - name: Installer le paquet openssh-server
          ansible.builtin.package:
            name: openssh-server
            state: present

        - name: Modifier la configuration SSH
          ansible.builtin.lineinfile:
            path: /etc/ssh/sshd_config
            regexp: '^PermitRootLogin'
            line: 'PermitRootLogin no'
            state: present
```

2. Lancez le playbook et vérifiez qu’il s’applique uniquement sur la machine
   Debian `server1`.

---

### ✏️ Étape 2 : Utilisation de `rescue` en cas d’échec

1. Modifiez le fichier précédent pour inclure un bloc `rescue:`

```yaml
- name: TP Blocks - Gestion du service SSH
  hosts: all
  tasks:
    - name: Gérer le service SSH sur Debian
      when: ansible_os_family == 'Debian'
      become: true
      tags: ssh
      block:
        - name: Tâche qui échoue volontairement
          ansible.builtin.command:
            cmd: /bin/false

        - name: Cette tâche ne sera pas exécutée
          ansible.builtin.debug:
            msg: "Succès"
      rescue:
        - name: Afficher un message d'erreur
          ansible.builtin.debug:
            msg: "Erreur détectée, exécution du plan B"

        - name: Tâche de contournement
          ansible.builtin.file:
            path: /tmp/plan_b.txt
            state: touch
            mode: '0644'
```

2. Vérifiez que le fichier `/tmp/plan_b.txt` est bien créé.

---

### ✏️ Étape 3 : Nettoyage avec `always`

1. Ajoutez une section `always:` au playbook:

```yaml
      always:
        - name: Nettoyage post-exécution
          ansible.builtin.debug:
            msg: "Fin du bloc, nettoyage terminé"
```

2. Le message doit s'afficher dans tous les cas.

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : vous devrez
créer un playbook qui gère l’installation du service SSH sur plusieurs systèmes
d’exploitation, en utilisant des blocks pour gérer les erreurs et les actions de
nettoyage. Le test doit être effectué sur les hôtes `server1` et `server2`.

---

## 🎯 Compétences acquises

* Organisation des tâches avec `block`
* Gestion des erreurs grâce à `rescue`
* Actions de post-traitement via `always`

Vous êtes maintenant capable de construire des playbooks robustes et lisibles ✨
