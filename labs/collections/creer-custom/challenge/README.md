# 🎯 Challenge — Initialiser et builder votre collection minimaliste

## ✅ Objectif

Initialiser une collection **`student.rhce.lab95`**, y ajouter **un module Python** qui retourne `"Hello, lab95!"`, builder le tarball, et prouver que la structure passe `ansible-test sanity --docker default --test ansible-doc`.

| Élément | Valeur attendue |
| --- | --- |
| Namespace | `student` |
| Nom collection | `lab95` |
| Version | `1.0.0` |
| Module custom | `plugins/modules/lab95_hello.py` qui retourne `msg="Hello, lab95!"` |
| Tarball | `build/student-lab95-1.0.0.tar.gz` |
| Tags `galaxy.yml` | au moins `[demo, lab95]` |

## 🧩 Indices

### Étape 1 — Init

```bash
cd labs/collections/creer-custom/challenge/
mkdir -p collection_root
ansible-galaxy collection init student.lab95 --init-path ???
```

### Étape 2 — Squelette du module Python

`collection_root/ansible_collections/student/lab95/plugins/modules/lab95_hello.py` :

```python
#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: lab95_hello
short_description: ???
version_added: ???
description:
  - ???
options: {}
author:
  - "Apprenant RHCE 2026"
'''

EXAMPLES = r'''
- name: Test hello
  student.lab95.lab95_hello:
'''

RETURN = r'''
msg:
  description: Message de salutation.
  type: str
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module = AnsibleModule(argument_spec=dict(), supports_check_mode=True)
    module.exit_json(changed=False, msg=???)


def main():
    run_module()


if __name__ == '__main__':
    main()
```

### Étape 3 — Compléter `galaxy.yml`

Vérifier la présence de :

```yaml
namespace: student
name: lab95
version: "1.0.0"
tags:
  - ???
  - ???
authors:
  - "???"
```

### Étape 4 — Compléter `meta/runtime.yml`

```yaml
---
requires_ansible: ???
```

### Étape 5 — Builder

```bash
cd collection_root/ansible_collections/student/lab95/
ansible-galaxy collection build --output-path ../../../../build/
ls ../../../../build/
```

> 💡 **Pièges** :
>
> - **Arborescence stricte** : `collection_root/ansible_collections/<namespace>/<name>/`.
>   Pas le bon chemin = collection invalide.
> - **`namespace.name`** : minuscules, underscores autorisés. Pas de
>   tiret. Pas de point. Validation stricte par Galaxy.
> - **`galaxy.yml`** obligatoire à la racine. Champs requis : `namespace`,
>   `name`, `version`, `readme`, `authors`. Sinon, `ansible-galaxy build`
>   refuse.
> - **`build_ignore:`** : exclure des fichiers du tarball (`tests/`,
>   `.git/`, `*.pyc`). Réduit la taille publié sur Galaxy.
> - **`ansible-galaxy collection install <tarball>`** pour tester
>   localement avant publish.

## 🚀 Lancement

```bash
cd labs/collections/creer-custom/challenge/
# Suivez les étapes ci-dessus pour produire build/student-lab95-1.0.0.tar.gz
```

## 🧪 Validation automatisée

```bash
pytest -v labs/collections/creer-custom/challenge/tests/
```

Le test pytest valide la **structure générée** : tarball présent, galaxy.yml conforme, module Python avec `DOCUMENTATION` + `RETURN`.

## 🧹 Reset

```bash
make -C labs/collections/creer-custom/ clean
```

## 💡 Pour aller plus loin

- **`ansible-test sanity --docker default --test ansible-doc`** dans la collection.
- **`ansible-galaxy collection publish ...`** vers Galaxy (token API requis).
- **`changelogs/fragments/`** : un YAML par PR plutôt qu'un CHANGELOG.rst monolithique.
