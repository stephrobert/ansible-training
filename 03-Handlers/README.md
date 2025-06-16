# 03 – Handlers et Notifications

Bienvenue dans le troisième TP de la formation Ansible ! Ce TP vous initie à
l’utilisation des **handlers**, une mécanique importante pour contrôler quand
certaines tâches doivent être exécutées.

---

## 🧠 Lecture recommandée

Avant de commencer, je vous recommande de lire cette section du guide : 🔗
[Templates et Handlers
(guide)](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecriture-de-playbooks-ansible/#utilisation-des-handlers-ansible)

Vous y apprendrez :

* Ce qu’est un handler dans Ansible
* Comment les déclencher via `notify`
* Leur exécution conditionnelle : uniquement si l’état d’une tâche change

---

## 🎯 Objectifs du TP

1. Créer une tâche modifiant un fichier de configuration
2. Notifier un handler seulement si la tâche a modifié le fichier
3. Implémenter un handler exécutant une commande ou affichant un message

---

## 📁 Arborescence

```bash
03-Handlers/
├── README.md
├── config-ssh.yml
└── challenge/
    ├── README.md
    └── tests/
        └── test_handler.py
```

---

## ⚙️ Étapes du TP

### Etape 0 : Prérequis

Commençons par créer un conteneur Incus pour ce TP. Assurez-vous d’avoir
installé Incus comme indiqué dans le README à la racine du projet.

```bash
incus launch images:ubuntu/24.04/cloud server1  --config=cloud-init.user-data="$(cat ../cloud-config.yaml)"
incus alias add login 'exec @ARGS@ -- su -l admin'
```

### Etape 1 : modification conditionnelle de la configuration SSH

Créez le fichier `config-ssh.yml` suivant :

```yaml
---
- name: TP Handlers - SSH
  hosts: server1
  connection: community.general.incus
  become: true
  tasks:

    - name: Installer le paquet openssh-server
      ansible.builtin.package:
        name: openssh-server
        state: present

    - name: Activer le service SSH
      ansible.builtin.service:
        name: ssh
        state: started
        enabled: true

    - name: Désactiver la connexion root via SSH
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PermitRootLogin'
        line: 'PermitRootLogin No'
        state: present
        backup: true
      notify: Restart_sshd

  handlers:
    - name: Restart_sshd
      ansible.builtin.service:
        name: ssh
        state: restarted
```

**Explications :**

- Ce playbook installe le paquet `openssh-server` et active le service SSH.
- Il modifie la configuration SSH pour désactiver la connexion root.
- La tâche `lineinfile` utilise `notify` pour déclencher le handler `Restart_sshd`
  uniquement si la ligne a été modifiée.
- Le handler redémarre le service SSH si la configuration a changé.
- Le handler est défini à la fin du playbook, il sera exécuté après toutes les
  tâches si nécessaire.

### Etape 2 : test de comportement

* Exécutez une première fois le playbook :

  ```bash
  ansible-playbook config-ssh.yml -i server1,
  ```

  Le handler doit s’exécuter.

* Exécutez une seconde fois :

  ```bash
  ansible-playbook config-ssh.yml -i server1,
  ```

  Le handler ne doit **pas** s'exécuter (fichier déjà en place, pas de
  changement).

### Etape 3 : nettoyage

Après avoir terminé le challenge, vous pouvez nettoyer le conteneur incus pour éviter les
conflits futurs :

```bash
incus delete server1 --force
```

---

## 🧪 Challenge à valider

Voir `challenge/README.md` pour la consigne du challenge final : Vous devrez
créer un handler exécutant une commande réelle (ex : créer un fichier
temporaire), et vérifier son exécution via un test `pytest` + `testinfra`.

---

## ✅ Compétences acquises

* Mécanisme de `notify` et `handlers`
* Exécution conditionnelle des handlers
* Débogage de leur comportement

Vous êtes maintenant prêt à combiner handlers et templates pour des déploiements
plus réactifs ❤️

🚀 En route vers le TP 04 sur les **Templates Jinja** Ansible !
