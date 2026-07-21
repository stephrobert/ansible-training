# 🎯 Challenge — Initialize and build your minimalist collection

## ✅ Objective

Initialize a collection **`student.lab95`**, add **a Python module** to it that returns `"Hello, lab95!"`, build the tarball, and prove that the structure passes `ansible-test sanity --docker default --test ansible-doc`.

| Element | Expected value |
| --- | --- |
| Namespace | `student` |
| Collection name | `lab95` |
| Version | `1.0.0` |
| Custom module | `plugins/modules/lab95_hello.py` that returns `msg="Hello, lab95!"` |
| Tarball | `build/student-lab95-1.0.0.tar.gz` |
| `galaxy.yml` tags | at least `[demo, lab95]` |

## 🧩 Hints

### Step 1 — Init

```bash
cd labs/collections/creer-custom/challenge/
mkdir -p collection_root
ansible-galaxy collection init student.lab95 --init-path ???
```

### Step 2 — Python module skeleton

`collection_root/ansible_collections/student/lab95/plugins/modules/lab95_hello.py`:

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

### Step 3 — Complete `galaxy.yml`

Check the presence of:

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

### Step 4 — Complete `meta/runtime.yml`

```yaml
---
requires_ansible: ???
```

### Step 5 — Build

```bash
cd collection_root/ansible_collections/student/lab95/
ansible-galaxy collection build --output-path ../../../../build/
ls ../../../../build/
```

> 💡 **Pitfalls**:
>
> - **Strict tree**: `collection_root/ansible_collections/<namespace>/<name>/`.
>   Wrong path = invalid collection.
> - **`namespace.name`**: lowercase, underscores allowed. No
>   hyphen. No dot. Strict validation by Galaxy.
> - **`galaxy.yml`** mandatory at the root. Required fields: `namespace`,
>   `name`, `version`, `readme`, `authors`. Otherwise, `ansible-galaxy build`
>   refuses.
> - **`build_ignore:`**: exclude files from the tarball (`tests/`,
>   `.git/`, `*.pyc`). Reduces the size published on Galaxy.
> - **`ansible-galaxy collection install <tarball>`** to test
>   locally before publish.

## 🚀 Launch

```bash
cd labs/collections/creer-custom/challenge/
# Follow the steps above to produce build/student-lab95-1.0.0.tar.gz
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/creer-custom/challenge/tests/
```

The pytest test validates the **generated structure**: tarball present, compliant galaxy.yml, Python module with `DOCUMENTATION` + `EXAMPLES` + `RETURN`.

## 🧹 Reset

```bash
dsoxlab clean collections-creer-custom
```

## 💡 Going further

- **`ansible-test sanity --docker default --test ansible-doc`** in the collection.
- **`ansible-galaxy collection publish ...`** to Galaxy (API token required).
- **`changelogs/fragments/`**: one YAML per PR rather than a monolithic CHANGELOG.rst.
