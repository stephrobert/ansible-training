# Lab 97 — Migration rôle standalone → collection avec `plugin_routing.redirect`

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo.

## 🧠 Rappel

🔗 [**Migration rôle → collection**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/migration-role/)

En 2026, **les rôles standalone Galaxy v1 sont legacy**. Galaxy NG (backend Galaxy v3) ne supporte **que** les collections. Si vous maintenez un rôle public, il faut le **migrer en collection** sans casser les playbooks downstream qui l'utilisent encore avec son ancien nom.

Mécanisme officiel : **`meta/runtime.yml`** avec **`plugin_routing.redirect`**. Un playbook qui invoque `webapp_module` continue de marcher (avec un **warning de dépréciation**) alors que le code réel vit désormais dans `mycoll.webapp.webapp_module`.

Ce lab pratique cette migration sur un mini-rôle, et **prouve** que les deux noms (ancien standalone + nouveau FQCN) fonctionnent.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Identifier** un rôle standalone candidat à la migration.
2. **Initialiser** la collection cible avec `ansible-galaxy collection init`.
3. **Déplacer** `tasks/`, `handlers/`, `defaults/`, `templates/` vers `roles/<name>/`.
4. **Déplacer** un module custom de `library/` vers `plugins/modules/`.
5. **Configurer `plugin_routing.redirect`** dans `meta/runtime.yml`.
6. **Tester** que l'ancien nom déclenche un warning de dépréciation **mais fonctionne**.
7. **Tester** que le nouveau FQCN est la cible recommandée.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible-galaxy --version

# Cleanup
rm -rf labs/collections/migration-role/{ansible_collections,roles_legacy} 2>/dev/null
```

## ⚙️ Arborescence cible

```text
labs/collections/migration-role/
├── README.md                                 ← ce fichier
├── Makefile                                  ← cible clean
├── roles_legacy/                             ← (à créer) rôle standalone d'origine
│   └── webapp/
│       ├── tasks/main.yml
│       └── library/
│           └── lab97_status.py               ← module custom (legacy emplacement)
├── ansible_collections/                      ← (généré par init) collection cible
│   └── student/
│       └── webapp/
│           ├── galaxy.yml
│           ├── meta/runtime.yml
│           ├── plugins/modules/lab97_status.py
│           └── roles/webapp/tasks/main.yml
└── challenge/
    ├── README.md
    └── tests/
        └── test_migration.py
```

L'apprenant écrit lui-même la collection cible et le `meta/runtime.yml`.

## 📚 Exercice 1 — Le point de départ : un rôle legacy

Créer le rôle standalone d'origine :

```bash
mkdir -p labs/collections/migration-role/roles_legacy/webapp/{tasks,library}
```

`labs/collections/migration-role/roles_legacy/webapp/tasks/main.yml` :

```yaml
---
- name: Status check via le module legacy lab97_status
  lab97_status:        # ← nom court (sans FQCN), legacy
  register: status

- ansible.builtin.debug:
    msg: "Statut: {{ status.msg }}"
```

`labs/collections/migration-role/roles_legacy/webapp/library/lab97_status.py` :

```python
#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
def main():
    AnsibleModule(argument_spec={}).exit_json(
        changed=False, msg="lab97-legacy-OK"
    )
if __name__ == "__main__":
    main()
```

🔍 **Observation** : c'est le **format historique** des rôles standalone : `tasks/main.yml` + un dossier `library/` qui contient les modules custom. Galaxy v1 acceptait ça. Galaxy NG **non**.

## 📚 Exercice 2 — Initialiser la collection cible

```bash
cd labs/collections/migration-role/
mkdir -p ansible_collections
ansible-galaxy collection init student.webapp \
  --init-path ansible_collections/
```

🔍 **Observation** : génère la structure conforme avec `roles/`, `plugins/modules/`, `meta/runtime.yml`, etc.

## 📚 Exercice 3 — Migrer le rôle dans `roles/`

```bash
mkdir -p ansible_collections/student/webapp/roles/webapp/tasks
cp roles_legacy/webapp/tasks/main.yml \
   ansible_collections/student/webapp/roles/webapp/tasks/main.yml
```

Adapter `tasks/main.yml` pour utiliser le **nouveau FQCN** :

```yaml
---
- name: Status check via le module migré
  student.webapp.lab97_status:    # ← nouveau FQCN
  register: status

- ansible.builtin.debug:
    msg: "Statut: {{ status.msg }}"
```

🔍 **Observation** : à l'**intérieur** de la collection, on peut écrire des noms courts (`lab97_status:`), mais c'est **déconseillé**. Le FQCN explicite reste **lisible** et **portable**.

## 📚 Exercice 4 — Migrer le module dans `plugins/modules/`

```bash
mkdir -p ansible_collections/student/webapp/plugins/modules
cp roles_legacy/webapp/library/lab97_status.py \
   ansible_collections/student/webapp/plugins/modules/lab97_status.py
```

Compléter le module avec les sections obligatoires `DOCUMENTATION`, `EXAMPLES`, `RETURN` :

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: lab97_status
short_description: Module de démonstration migré du rôle standalone vers une collection
version_added: "1.0.0"
description:
  - Retourne un statut OK pour valider la migration.
options: {}
author:
  - "Apprenant RHCE 2026"
'''

EXAMPLES = r'''
- name: Status check
  student.webapp.lab97_status:
'''

RETURN = r'''
msg:
  description: Message de statut.
  type: str
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule

def main():
    AnsibleModule(argument_spec={}).exit_json(changed=False, msg="lab97-migrated-OK")

if __name__ == "__main__":
    main()
```

🔍 **Observation** : `plugins/modules/<name>.py` est l'**emplacement standard**. Le `library/` legacy à la racine du rôle n'est **plus reconnu** dès qu'un rôle vit dans une collection.

## 📚 Exercice 5 — Configurer `plugin_routing.redirect` dans `meta/runtime.yml`

C'est **le cœur** de la migration : permettre à un playbook qui invoque l'**ancien nom court** `lab97_status:` de continuer à marcher.

`ansible_collections/student/webapp/meta/runtime.yml` :

```yaml
---
requires_ansible: ">=2.18.0"

plugin_routing:
  modules:
    lab97_status:
      redirect: student.webapp.lab97_status
      deprecation:
        removal_version: 2.0.0
        warning_text: |
          Le module 'lab97_status' (rôle standalone) est déprécié.
          Utilisez 'student.webapp.lab97_status' (FQCN collection).
```

🔍 **Observation cruciale** : **`plugin_routing.modules.<old_name>.redirect`** déclare la cible. **`deprecation:`** ajoute un **warning** au runtime mais **n'échoue pas**. **`removal_version`** indique quand l'alias sera retiré (semver de la collection). Pattern essentiel pour la rétrocompatibilité.

## 📚 Exercice 6 — Tester l'ancien nom + le nouveau FQCN

Créer un playbook de test :

```yaml
---
- hosts: db1.lab
  collections:
    - student.webapp           # ← ne déclare que la collection (rétro-compat)
  tasks:
    - name: Test ancien nom court (avec deprecation warning)
      lab97_status:             # ← l'ancien nom, qui sera redirigé
      register: legacy

    - name: Test nouveau FQCN explicite
      student.webapp.lab97_status:
      register: new

    - ansible.builtin.copy:
        dest: /tmp/lab97-migration.txt
        content: |
          legacy: {{ legacy.msg }}
          new: {{ new.msg }}
        mode: "0644"
```

Lancer :

```bash
ANSIBLE_COLLECTIONS_PATH=labs/collections/migration-role/ansible_collections \
  ansible-playbook lab.yml
```

Sortie attendue :

```text
[DEPRECATION WARNING]: Le module 'lab97_status' (rôle standalone) est déprécié...
TASK [Test ancien nom court (avec deprecation warning)] ***
ok: [db1.lab]
TASK [Test nouveau FQCN explicite] ***
ok: [db1.lab]
```

🔍 **Observation** : les **deux noms fonctionnent**. L'ancien nom déclenche un **warning** mais ne casse pas. Les playbooks downstream peuvent migrer **progressivement** vers le FQCN.

## 📚 Exercice 7 — Builder + publier la collection migrée

```bash
cd ansible_collections/student/webapp/
ansible-galaxy collection build --output-path ../../../build/
ls ../../../build/
```

Sortie : `student-webapp-1.0.0.tar.gz` prêt à `publish`.

🔍 **Observation** : la collection est **publiable** sur Galaxy. Les utilisateurs migrent progressivement leurs playbooks vers le FQCN au gré des releases mineures, et au bump majeur (v2.0.0) on retire l'alias.

## 🔍 Observations à noter

- **Rôles standalone** = legacy. Galaxy NG ne supporte que les collections.
- **Migration** = `tasks/`, `handlers/`, `defaults/` → `roles/<name>/`. `library/` → `plugins/modules/`.
- **`plugin_routing.redirect`** dans `meta/runtime.yml` permet la rétrocompatibilité.
- **`deprecation:`** ajoute un warning au runtime + `removal_version` planifie la suppression.
- **L'ancien nom** continue de marcher — les downstream migrent progressivement.

## 🤔 Questions de réflexion

1. Que se passe-t-il si on **renomme un module sans `plugin_routing.redirect`** ?
2. Pourquoi le `library/` legacy d'un rôle dans une collection est-il **ignoré** ?
3. Comment **forcer l'échec** d'un playbook qui utilise un nom déprécié ? (Indice : `ANSIBLE_DEPRECATION_WARNINGS=True` + `ANSIBLE_DISPLAY_TRACEBACK=deprecate`).
4. **Cas limite** : si deux collections déclarent un redirect vers le même nom court, laquelle gagne ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — migrer un rôle `legacy_role` vers `student.lab97_migrated`, configurer un `plugin_routing` qui rediriger l'ancien module, et prouver que les **deux noms fonctionnent**.

## 💡 Pour aller plus loin

- **Pages MDX collections** : la section complète sur le blog.
- **`ansible-galaxy collection install student.webapp:1.0.0`** : installation depuis un Hub privé.
- **Antsibull-changelog** : génération de `CHANGELOG.rst` à partir de fragments.
- **Galaxy NG**: backend Pulp-based pour Automation Hub privé.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile production \
  labs/collections/migration-role/ansible_collections/student/webapp/
```
