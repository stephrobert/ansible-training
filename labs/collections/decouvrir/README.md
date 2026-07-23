# Lab 93 — Discover Ansible collections (FQCN, structure, `ansible-galaxy`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Discover Ansible collections**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/)

A **collection** is the modern distribution unit for Ansible **modules**, **plugins** (filter, lookup, inventory…), **roles**, **playbooks** and **docs**. It definitively replaces the standalone Galaxy v1 roles.

Every Ansible resource is now named with an **FQCN** (Fully Qualified Collection Name): **`namespace.collection.plugin`**. Examples: `ansible.builtin.copy`, `community.general.archive`, `kubernetes.core.k8s`. This FQCN becomes **mandatory** on all RHCE 2026 playbooks (`fqcn-builtins` rule of `ansible-lint --profile production`).

This lab explores the collections **already installed** in your EE / venv: structure, metadata, available modules, dependencies between collections.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **List** all installed collections (`ansible-galaxy collection list`).
2. **Inspect** a specific collection (`ansible-galaxy collection info`).
3. **Read** a `galaxy.yml` (metadata + dependencies + tags).
4. **Understand** the standard structure `plugins/`, `roles/`, `playbooks/`, `meta/runtime.yml`.
5. **Distinguish** a **standalone role** from a **role in a collection**.
6. **Find** a module with its FQCN via `ansible-doc -l | grep`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible-galaxy --version
ansible-galaxy collection install community.general --force 2>&1 | tail -3
```

## ⚙️ Target layout

```text
labs/collections/decouvrir/
├── README.md              ← this file (guided tutorial)
└── challenge/
    ├── README.md          ← the challenge brief
    └── tests/
        └── test_decouvrir.py
```

The learner writes `lab.yml` themselves (as the exercises go) and `challenge/solution.yml`.

## 📚 Exercise 1 — List installed collections

```bash
ansible-galaxy collection list
```

Typical output:

```text
# /usr/share/ansible/collections/ansible_collections
Collection                    Version
----------------------------- -------
ansible.posix                 2.0.0
community.general             10.5.0
kubernetes.core               5.1.1

# ~/.ansible/collections/ansible_collections
Collection                    Version
----------------------------- -------
community.docker              4.0.0
```

🔍 **Observation**: the command **aggregates** all the sources: system (`/usr/share/ansible/`), user (`~/.ansible/`), virtualenv. Several versions of the same collection can coexist: the one used depends on the order in **`ANSIBLE_COLLECTIONS_PATH`**.

## 📚 Exercise 2 — Inspect a specific collection

```bash
ansible-galaxy collection info community.general
```

Output:

```text
Collection: community.general
Version: 10.5.0
Path: /usr/share/ansible/collections/ansible_collections/community/general
Documentation: https://docs.ansible.com/ansible/latest/collections/community/general/
Repository: https://github.com/ansible-collections/community.general
Issues: https://github.com/ansible-collections/community.general/issues
License: GPL-3.0-or-later
Authors:
  - Ansible Community
```

🔍 **Observation**: it is the equivalent of `dnf info` or `apt show`. **Reference** to verify that a collection really comes from public Galaxy and not from a compromised source.

## 📚 Exercise 3 — Read the `galaxy.yml`

```bash
cat /usr/share/ansible/collections/ansible_collections/community/general/galaxy.yml | head -30
```

Key fields:

| Field | Role |
|-------|------|
| `namespace` | FQCN prefix (e.g. `community`, `kubernetes`, `acme`) |
| `name` | Short name of the collection |
| `version` | Strict semver (e.g. `10.5.0`) |
| `dependencies` | Other required collections (with version constraints) |
| `tags` | Categories (`linux`, `web`, `cloud`, `kubernetes`) |
| `repository` | URL of the source Git repo |
| `documentation` | URL of the generated doc |

🔍 **Observation**: `tags:` is **mandatory** to publish on Galaxy. Without tags, the import fails with an unclear message.

## 📚 Exercise 4 — Explore the internal structure

```bash
tree -L 2 /usr/share/ansible/collections/ansible_collections/community/general/
```

Typical output:

```text
community.general/
├── galaxy.yml
├── README.md
├── meta/
│   └── runtime.yml
├── plugins/
│   ├── modules/        ← Python modules (e.g. archive.py)
│   ├── filter/         ← custom Jinja2 filters
│   ├── lookup/         ← lookup plugins
│   ├── inventory/      ← inventory plugins
│   └── callback/       ← callback plugins
├── roles/              ← included roles
├── playbooks/          ← provided playbooks
├── changelogs/
└── docs/
```

🔍 **Observation**: the structure is **fixed** since ansible-core 2.10. A custom module **must** be in `plugins/modules/`, never at the root nor in a `library/` (legacy).

## 📚 Exercise 5 — `meta/runtime.yml` and the ansible-core threshold

```bash
cat /usr/share/ansible/collections/ansible_collections/community/general/meta/runtime.yml | head -10
```

Typical example:

```yaml
---
requires_ansible: ">=2.15.0"

plugin_routing:
  modules:
    sudoers:
      redirect: community.general.sudoers
```

🔍 **Crucial observation**: **`requires_ansible:`** declares the minimum ansible-core version. **`plugin_routing.redirect`** is used when a module is renamed: a playbook that uses the old name keeps working with a deprecation warning. Essential pattern for backward compatibility.

## 📚 Exercise 6 — Find a module via FQCN

```bash
# List all modules of a collection
ansible-doc -l community.general | head -10

# Find a module by keyword
ansible-doc -l | grep -i archive

# Read a module's doc
ansible-doc community.general.archive
```

Output:

```text
> COMMUNITY.GENERAL.ARCHIVE    (.../archive.py)

  Creates or extends an archive...

OPTIONS (= is mandatory):
- dest
        The file name of the destination archive...
- format
        The type of compression to use.
        choices:
        - "bz2", "gz", "tar", "xz", "zip"
```

🔍 **Observation**: `ansible-doc <FQCN>` is **the** reference to check the parameters before using a module. Prefer it over the internet doc: the doc shown is that of the **installed version**.

## 📚 Exercise 7 — Difference between standalone role and role in a collection

Galaxy distributes **two types** of content:

| Type | Distribution | Installation | Usage |
|------|-------------|--------------|-------|
| **Standalone role** | `ansible-galaxy role install geerlingguy.docker` | `~/.ansible/roles/geerlingguy.docker/` | `roles: [geerlingguy.docker]` |
| **Role in a collection** | `ansible-galaxy collection install community.general` | `~/.ansible/collections/.../community/general/roles/` | `roles: [community.general.bind]` |

🔍 **Observation**: the **standalone** format is **legacy**. Every new distribution publishes as a **collection**. Galaxy NG (Galaxy v3 backend, 2026) supports **only** collections.

## 🔍 Observations to note

- **FQCN** = `namespace.collection.plugin`, **mandatory** in 2026.
- **`ansible-galaxy collection list/info`** to explore what is installed.
- **`galaxy.yml`**: metadata + dependencies + tags.
- **`meta/runtime.yml`**: ansible-core threshold + module redirects.
- **Fixed structure**: `plugins/{modules,filter,lookup,inventory,callback}/`, `roles/`, `playbooks/`, `docs/`.
- **`ansible-doc`**: doc of the installed version, more reliable than the internet.

## 🤔 Reflection questions

1. What happens if **two versions** of `community.general` are installed in different paths?

2. Why did the FQCN become **mandatory** when short names worked before?

3. How do you know **all** the **dependency** collections of a given collection?

4. What is **`build_ignore:`** used for in `galaxy.yml`? (Hint: exclude `.git/`, `.venv/`, test secrets from the published tarball).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): produce an inventory file of the installed collections with **their versions** and their **path**, deposited on `db1.lab`.

## 💡 Going further

- **Lab 94**: complete `requirements.yml` (Galaxy + Git + GPG signatures).
- **Lab 95**: create **your own collection** with `ansible-galaxy collection init`.
- **Public Galaxy vs Automation Hub**: two registries, two ecosystems.
- **Red Hat Validated Content**: collections **certified + signed + Trivy scanned**.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/collections/decouvrir/lab.yml
ansible-lint labs/collections/decouvrir/challenge/solution.yml
ansible-lint --profile production labs/collections/decouvrir/challenge/solution.yml
```

> 💡 **Tip**: the **`fqcn-builtins`** rule of ansible-lint flags any module used without FQCN. Essential to prepare the RHCE.
