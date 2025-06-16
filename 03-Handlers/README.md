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
    - name: Désactiver la connexion root via SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^PermitRootLogin'
        line: 'PermitRootLogin No'
        state: present
        backup: true
      notify: restart_sshd

  handlers:
    - name: restart_sshd
      service:
        name: sshd
        state: restarted
```

- Cette tâche modifie (ou ajoute) la ligne `PermitRootLogin No` dans `/etc/ssh/sshd_config`.
- Le handler redémarre le service SSH **uniquement si la configuration a changé**.
- Utilisez `become: true` car la modification nécessite les droits root.

### Etape 2 : test de comportement

* Exécutez une première fois le playbook :

  ```bash
  ansible-playbook config-ssh.yml
  ```

  Le handler doit s’exécuter.

* Exécutez une seconde fois :

  ```bash
  ansible-playbook config-ssh.yml
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
