# Lab 58 — Créer son premier rôle Ansible (rôle fil rouge `webserver`)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Rappel

🔗 [**Créer son premier rôle Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/creer-premier-role/)

Un **rôle Ansible** est l'unité de réutilisation : un dossier structuré qui packagde tâches, variables, templates, handlers et tests autour d'un objectif unique. C'est **l'équivalent d'un module Terraform** côté Ansible.

Ce lab introduit le **rôle fil rouge** `webserver` qui sera enrichi au fil des labs 58 → 64. À la fin de cette série, vous aurez un rôle **production-ready** testé en TDD avec Molecule et tox.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Générer la structure d'un rôle avec **`ansible-galaxy role init`**.
2. Identifier les **10 dossiers** standards d'un rôle.
3. Écrire les **tâches principales** dans `tasks/main.yml`.
4. Définir les **variables par défaut** dans `defaults/main.yml`.
5. Documenter le rôle via **`meta/main.yml`** et **`README.md`**.
6. Appeler le rôle depuis un playbook avec **`roles:`**.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training/labs/roles/creer-premier-role
```

## ⚙️ Arborescence cible

```text
labs/roles/creer-premier-role/
├── README.md           ← ce fichier
├── inventory/          ← inventaire local du lab
├── playbook.yml        ← À CRÉER : appelle le rôle webserver
├── roles/
│   └── webserver/      ← rôle fil rouge (déjà créé)
│       ├── tasks/main.yml
│       ├── defaults/main.yml
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       └── README.md
└── challenge/
    ├── README.md       ← challenge final
    ├── solution.yml    ← À CRÉER : reproduire le rôle sur db1.lab
    └── tests/
        └── test_webserver.py
```

## 📚 Exercice 1 — Inspecter la structure du rôle

```bash
tree roles/webserver/
```

Sortie attendue :

```text
roles/webserver/
├── README.md
├── defaults/
│   └── main.yml
├── files/
├── handlers/
│   └── main.yml
├── meta/
│   └── main.yml
├── tasks/
│   └── main.yml
├── templates/
└── vars/
```

🔍 **Observation** : la structure est identique à ce que génère `ansible-galaxy role init webserver`. Les dossiers vides (`files/`, `templates/`, `vars/`) sont créés par `init` même s'ils ne contiennent rien — convention pour signaler qu'ils existent.

## 📚 Exercice 2 — Lire `tasks/main.yml`

```bash
cat roles/webserver/tasks/main.yml
```

3 tâches : installation, démarrage, ouverture firewall. **FQCN partout**, idempotence garantie par les modules dédiés.

🔍 **Observation à anticiper** : aucune **variable** dans ces tâches pour l'instant. Le rôle est **rigide** — il installe forcément nginx avec la config par défaut. Le lab 59 introduit les variables pour rendre le rôle paramétrable.

## 📚 Exercice 3 — Lire `defaults/main.yml`

```bash
cat roles/webserver/defaults/main.yml
```

3 variables avec valeurs par défaut. Préfixées par **`webserver_`** (convention nom du rôle pour éviter les collisions).

🔍 **Observation** : les variables ne sont **pas encore utilisées** dans `tasks/main.yml`. Le lab 59 les branchera correctement.

## 📚 Exercice 4 — Écrire le playbook racine

Créez `playbook.yml` à la racine du lab :

```yaml
---
- name: Déployer le rôle webserver
  hosts: web1.lab
  become: true

  roles:
    - role: webserver
```

🔍 **Observation** : pas de `tasks:` dans le playbook — toutes les tâches viennent du rôle. C'est le pattern recommandé : **playbooks fins, rôles épais**.

## 📚 Exercice 5 — Exécuter le playbook

```bash
ansible-playbook playbook.yml
```

Sortie attendue :

```text
PLAY [Déployer le rôle webserver] *********************************

TASK [Gathering Facts] *****************************************
ok: [web1.lab]

TASK [webserver : Installer nginx] *****************************
changed: [web1.lab]

TASK [webserver : Démarrer et activer nginx] *******************
changed: [web1.lab]

TASK [webserver : Ouvrir le service HTTP dans firewalld] *******
changed: [web1.lab]

PLAY RECAP *****************************************************
web1.lab : ok=4 changed=3 unreachable=0 failed=0
```

🔍 **Observation** : les tâches sont **préfixées par `webserver :`** dans la sortie — Ansible identifie clairement le rôle exécutant. Très utile pour debugger un play multi-rôles.

## 📚 Exercice 6 — Vérifier l'idempotence

Relancez :

```bash
ansible-playbook playbook.yml
```

Sortie attendue : `changed=0`. Tous les modules sont idempotents — re-jouer ne change rien.

## 📚 Exercice 7 — Tester nginx

```bash
curl http://web1.lab/
```

Sortie attendue : la page d'accueil par défaut de nginx (Welcome to nginx).

## 🔍 Observations à noter

- **Idempotence** : un second run de votre solution doit afficher `changed=0`
  partout dans le `PLAY RECAP`. C'est le signal mécanique d'un playbook
  conforme aux bonnes pratiques.
- **FQCN explicite** : préférez toujours `ansible.builtin.<module>` (ou la
  collection appropriée) plutôt que le nom court — `ansible-lint --profile
  production` le vérifie.
- **Convention de ciblage** : ce lab cible db1.lab ; pour adapter à un
  autre groupe, ajustez `hosts:` dans `lab.yml`/`solution.yml` puis relancez.
- **Reset isolé** : `make clean` à la racine du lab désinstalle proprement
  ce que la solution a posé pour pouvoir rejouer le scénario.

## 🤔 Questions de réflexion

1. Pourquoi placer les variables dans `defaults/` plutôt que dans `vars/` ?
2. Que se passe-t-il si vous changez `webserver_state` à `absent` dans le playbook (`vars: webserver_state: absent`) ?
3. Pourquoi `firewalld:` est-il dans la collection `ansible.posix` et pas `ansible.builtin` ?

## 🚀 Challenge final

Le challenge ([`challenge/README.md`](challenge/README.md)) demande de **reproduire le déploiement** sur `db1.lab` (mais avec `httpd` à la place de `nginx`) en réutilisant le rôle. Tests automatisés via `pytest+testinfra` :

```bash
pytest -v challenge/tests/
```

## 💡 Pour aller plus loin

- **Le rôle est ultra-simple** : pas de variables effectives dans les tâches, pas de templates, pas de validation. Le lab 59 introduit les variables.
- **`ansible-galaxy role init webserver`** génère la même structure que ce qu'on a ici — utile à savoir au RHCE.
- **Pattern de production** : un dossier `roles/` à la racine du repo, un sous-dossier par rôle. Les playbooks dans un dossier `playbooks/`.
- **Limite actuelle** : ce rôle ne marche QUE sur RHEL/Alma (à cause de `dnf`). Le lab 59 explorera la portabilité Debian/Ubuntu.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
ansible-lint labs/roles/creer-premier-role/lab.yml
ansible-lint labs/roles/creer-premier-role/challenge/solution.yml
ansible-lint --profile production labs/roles/creer-premier-role/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un
> hook pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
