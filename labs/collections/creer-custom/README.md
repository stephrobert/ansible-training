# Lab 95 — Construire votre propre collection (`student.rhce.webapp`)

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

🔗 [**Construire une collection Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/creer-collection/)

Une **collection custom** est l'aboutissement du parcours collections : packager **plusieurs ressources** (modules + rôles + plugins + playbooks) sous un même **namespace versionné**, distribuable, versionnable, testable.

Ce lab construit **`student.rhce.webapp`** : une collection minimaliste avec un **rôle `nginx`**, un **module Python custom** `webapp_healthcheck`, et un **playbook** d'orchestration. Validation par **`ansible-test sanity --docker`** au vert.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Initialiser** une collection avec `ansible-galaxy collection init`.
2. Comprendre la **structure standard** générée (`plugins/`, `roles/`, `playbooks/`, `meta/`, `tests/`).
3. **Remplir `galaxy.yml`** : namespace, name, version, dependencies, tags.
4. **Ajouter un rôle** dans `roles/<role_name>/`.
5. **Ajouter un module Python custom** dans `plugins/modules/`.
6. **Builder** la collection (`ansible-galaxy collection build`) → tarball.
7. **Tester** avec **`ansible-test sanity --docker default`**.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible all -m ansible.builtin.ping
ansible-galaxy --version
ansible-test --version

# Cleanup
rm -rf labs/collections/creer-custom/build/ \
       labs/collections/creer-custom/ansible_collections/ 2>/dev/null
```

## ⚙️ Arborescence cible (générée par `ansible-galaxy collection init`)

```text
labs/collections/creer-custom/
├── README.md                           ← ce fichier (tuto guidé)
├── Makefile                            ← cible clean
├── ansible_collections/                ← (généré par init)
│   └── student/
│       └── rhce/
│           ├── webapp/                 ← votre collection ici
│           │   ├── galaxy.yml
│           │   ├── README.md
│           │   ├── meta/
│           │   │   └── runtime.yml
│           │   ├── plugins/
│           │   │   └── modules/
│           │   │       └── webapp_healthcheck.py
│           │   ├── roles/
│           │   │   └── nginx/
│           │   │       └── tasks/main.yml
│           │   ├── playbooks/
│           │   │   └── deploy.yml
│           │   └── tests/
│           │       └── sanity/
└── challenge/
    ├── README.md
    └── tests/
        └── test_creer_custom.py
```

L'apprenant écrit lui-même le contenu de la collection (galaxy.yml, modules, rôles).

## 📚 Exercice 1 — Initialiser la collection

```bash
cd labs/collections/creer-custom/
mkdir -p ansible_collections
ansible-galaxy collection init student.rhce.webapp \
  --init-path ansible_collections/
```

Sortie :

```text
- Collection student.rhce.webapp was created successfully
```

```bash
tree ansible_collections/student/rhce/webapp/ -L 2
```

🔍 **Observation** : `init` génère **toute la structure** d'une collection conforme. Vous y trouvez `galaxy.yml`, `README.md`, `LICENSE`, `meta/runtime.yml`, `plugins/{modules,filter,...}/`, `roles/`, `playbooks/`, `tests/`. Pas besoin de tout remplir : ne garder que ce dont on a besoin.

## 📚 Exercice 2 — Remplir `galaxy.yml`

Éditer `ansible_collections/student/rhce/webapp/galaxy.yml` :

```yaml
namespace: student
name: rhce_webapp
version: 1.0.0
readme: README.md
authors:
  - "Apprenant RHCE 2026 <student@example.com>"
description: "Collection lab 95 — déploie webapp avec nginx"
license:
  - GPL-3.0-or-later
tags:
  - linux
  - web
  - nginx
dependencies:
  ansible.posix: ">=2.0.0"
repository: https://github.com/student/rhce-webapp
documentation: https://github.com/student/rhce-webapp
issues: https://github.com/student/rhce-webapp/issues
build_ignore:
  - .github
  - .venv
  - tests/output
```

🔍 **Observation cruciale** : **`tags:`** est **obligatoire** pour publier sur Galaxy. Sans, l'import échoue silencieusement. **`dependencies:`** déclare les autres collections requises avec contraintes semver.

## 📚 Exercice 3 — Remplir `meta/runtime.yml`

Éditer `ansible_collections/student/rhce/webapp/meta/runtime.yml` :

```yaml
---
requires_ansible: ">=2.18.0"
```

🔍 **Observation** : **`requires_ansible:`** est **obligatoire** dès qu'on ajoute un module Python custom. Sans, `ansible-test sanity` échoue. C'est la déclaration du **seuil minimum d'ansible-core** sur lequel la collection est garantie de fonctionner.

## 📚 Exercice 4 — Ajouter un rôle `nginx`

Créer `ansible_collections/student/rhce/webapp/roles/nginx/tasks/main.yml` :

```yaml
---
- name: Installer nginx
  ansible.builtin.dnf:
    name: nginx
    state: present

- name: Activer et démarrer nginx
  ansible.builtin.systemd_service:
    name: nginx
    state: started
    enabled: true
```

🔍 **Observation** : un rôle **dans une collection** suit la même structure qu'un rôle standalone (`tasks/`, `handlers/`, `defaults/`, `templates/`...). La différence : on l'utilise avec son **FQCN** : `student.rhce.webapp.nginx`.

## 📚 Exercice 5 — Ajouter un module Python custom

Créer `ansible_collections/student/rhce/webapp/plugins/modules/webapp_healthcheck.py` :

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: webapp_healthcheck
short_description: Health check minimaliste d'une URL HTTP
version_added: "1.0.0"
description:
  - Vérifie qu'une URL HTTP répond avec un code 200.
options:
  url:
    description: URL à tester.
    required: true
    type: str
author:
  - "Apprenant RHCE 2026"
'''

EXAMPLES = r'''
- name: Vérifier que nginx répond
  student.rhce.webapp.webapp_healthcheck:
    url: "http://localhost:80"
'''

RETURN = r'''
status_code:
  description: Code HTTP retourné.
  type: int
  returned: always
'''

import urllib.request
from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(url=dict(type='str', required=True))
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    url = module.params['url']
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            code = response.getcode()
        module.exit_json(changed=False, status_code=code)
    except Exception as exc:
        module.fail_json(msg=f"Health check KO: {exc}")


def main():
    run_module()


if __name__ == '__main__':
    main()
```

🔍 **Observation** : tous les modules Python suivent ce squelette : `DOCUMENTATION`, `EXAMPLES`, `RETURN` en YAML inline + `AnsibleModule` du `module_utils`. **`ansible-test sanity`** vérifie ces 3 sections.

## 📚 Exercice 6 — Ajouter un playbook d'orchestration

Créer `ansible_collections/student/rhce/webapp/playbooks/deploy.yml` :

```yaml
---
- name: Déployer la webapp avec la collection student.rhce.webapp
  hosts: webservers
  become: true
  tasks:
    - name: Appliquer le rôle nginx
      ansible.builtin.import_role:
        name: student.rhce.webapp.nginx     # ← FQCN du rôle

    - name: Health check via le module custom
      student.rhce.webapp.webapp_healthcheck:    # ← FQCN du module
        url: "http://localhost:80"
      register: hc

    - ansible.builtin.debug:
        var: hc.status_code
```

🔍 **Observation** : depuis l'extérieur de la collection, on appelle modules et rôles avec **leur FQCN complet**. À l'intérieur d'une collection, on peut utiliser des noms courts (mais déconseillé pour la lisibilité).

## 📚 Exercice 7 — Builder la collection

```bash
cd ansible_collections/student/rhce/webapp/
ansible-galaxy collection build --output-path ../../../../build/
```

Sortie :

```text
Created collection for student.rhce.webapp at /home/.../build/student-rhce_webapp-1.0.0.tar.gz
```

```bash
ls -la ../../../../build/
```

🔍 **Observation** : le **tarball** est **publiable** sur Galaxy avec `ansible-galaxy collection publish <tarball> --token "$GALAXY_TOKEN"`. Versions automatiques via CI : tag Git `v1.0.0` → workflow build → publish.

## 📚 Exercice 8 — Lancer `ansible-test sanity`

```bash
cd ansible_collections/student/rhce/webapp/
ansible-test sanity --docker default -v
```

Cible :

```text
Running sanity test "ansible-doc"
Running sanity test "validate-modules"
Running sanity test "yamllint"
Running sanity test "pep8"
...
All sanity tests passed.
```

🔍 **Observation** : **`ansible-test sanity --docker`** lance **dans un conteneur** une batterie de validations : doc YAML cohérente, types Python, FQCN, PEP8, yamllint. **Indispensable en CI** avant publication. Sans, l'import Galaxy échoue silencieusement.

## 🔍 Observations à noter

- **`ansible-galaxy collection init`** génère la structure complète conforme.
- **`galaxy.yml`** : namespace, name, version semver, **`tags:` obligatoire**, dependencies.
- **`meta/runtime.yml`** : **`requires_ansible:`** obligatoire dès qu'on a un module Python.
- **Module Python** : `DOCUMENTATION` + `EXAMPLES` + `RETURN` en YAML + `AnsibleModule`.
- **FQCN** depuis l'extérieur de la collection : `namespace.collection.plugin`.
- **`ansible-galaxy collection build`** produit un tarball publiable.
- **`ansible-test sanity --docker default`** valide doc + types + FQCN + PEP8.

## 🤔 Questions de réflexion

1. Pourquoi un **`namespace`** sur Galaxy doit-il être **réservé** avant de publier ? (Indice : éviter les **typosquatting attacks**).

2. Que se passe-t-il si on publie **sans `tags:`** dans `galaxy.yml` ? (Indice : import Galaxy KO).

3. À quoi sert **`build_ignore:`** ? (Indice : exclure `.git/`, `.venv/`, secrets de tests du tarball).

4. Comment gérer une **breaking change** sur le module ? (Indice : bump majeur + `meta/runtime.yml plugin_routing.deprecation`).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) — initialiser une collection minimaliste avec **un rôle simple** + **un module Python qui retourne `Hello`**, builder le tarball, prouver qu'il est publiable.

## 💡 Pour aller plus loin

- **Lab 96** : pipeline CI matrice ansible-core × Python.
- **Lab 97** : migration rôle standalone → collection.
- **Changelog fragmenté** : `changelogs/fragments/<NN>-<desc>.yml` au lieu d'un `CHANGELOG.rst` monolithique.
- **Galaxy NG** local : déployer un Automation Hub privé.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint --profile production \
  labs/collections/creer-custom/ansible_collections/student/rhce/webapp/
```
