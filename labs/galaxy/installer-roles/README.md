# Lab 74 — `requirements.yml`: install roles & collections from Galaxy / Git

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Ansible installed. No VMs needed (purely local lab).

## 🧠 Recap

🔗 [**Installing roles via requirements.yml**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/installer-roles-galaxy/)

A `requirements.yml` file is the **Ansible equivalent** of `package.json`
(Node), `requirements.txt` (Python) or `Gemfile` (Ruby). It declares **all
the dependencies** of a project (roles **and** collections) with sources
(Galaxy or Git) and pinned versions.

```yaml
# requirements.yml
roles:
  - name: geerlingguy.docker      # Galaxy
    version: 7.4.4

  - src: https://github.com/foo/bar    # Git
    name: foo.bar
    version: v1.2.0

collections:
  - name: ansible.posix
    version: ">=1.5.0,<2.0.0"          # SemVer range
```

→ Installation: `ansible-galaxy install -r requirements.yml` (roles)
+ `ansible-galaxy collection install -r requirements.yml` (collections).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a **`requirements.yml`** mixing Galaxy roles + Git + collections.
2. **Pin versions** (exact, SemVer range, Git tag, branch).
3. Distinguish **Galaxy** (author.role) from **Git** (cloneable URL).
4. Understand `~/.ansible/roles/` vs `~/.ansible/collections/`.
5. **Vendor** a role into the repo (`-p roles/`).
6. Prepare a **reproducible** Ansible project (versioned `requirements.yml`).

## 🔧 Preparation

```bash
ansible-galaxy --version
```

## ⚙️ Directory tree

```text
labs/galaxy/installer-roles/
├── README.md
├── requirements.yml         ← the manifest to study
└── roles/                    ← local install target (vendoring)
```

## 📚 Exercise 1 — Read the shipped `requirements.yml`

```yaml
---
roles:
  # 1. Public Galaxy role (with pinned version)
  - name: geerlingguy.docker
    version: 7.4.4

  # 2. Role from Git (main branch)
  - src: https://github.com/stephrobert/ansible-role-motd
    name: stephrobert.motd
    version: main

  # 3. Role from Git with tag
  - src: https://github.com/geerlingguy/ansible-role-postgresql
    name: geerlingguy.postgresql
    version: 4.1.0

collections:
  - name: ansible.posix
    version: ">=1.5.0,<2.0.0"

  - name: community.general
    version: ">=8.0.0"

  - name: community.crypto
    version: "2.20.0"          # ← exact match production

  - name: ansible.utils
    version: ">=4.0.0"
```

🔍 **Observation**: 3 roles (1 Galaxy + 2 Git) and 4 collections.
Each **pins** its version for reproducibility.

## 📚 Exercise 2 — Install into `~/.ansible/`

```bash
cd labs/galaxy/installer-roles/
ansible-galaxy role install -r requirements.yml
ansible-galaxy collection install -r requirements.yml

ansible-galaxy role list
ansible-galaxy collection list
```

🔍 **Observation**: by default, roles go into `~/.ansible/roles/` and
collections into `~/.ansible/collections/ansible_collections/`.

## 📚 Exercise 3 — Vendor into the project's `roles/`

```bash
ansible-galaxy role install -r requirements.yml -p roles/
ansible-galaxy collection install -r requirements.yml -p collections/
```

🔍 **Observation**: `-p` (path) installs **into the repo itself**. This is
the **vendoring** pattern: you commit the third-party roles to have a
reproducible project **without network**.

> ⚠️ **No absolute standard**: some commit them (security,
> reproducibility), others do not (repo size). The versioned
> `requirements.yml` is enough in most cases.

## 📚 Exercise 4 — Fine-grained pinning (versions, tags, branches)

| Form | Example | Effect |
| --- | --- | --- |
| Exact Galaxy version | `version: 7.4.4` | Strict reproducible |
| SemVer range | `version: ">=1.5.0,<2.0.0"` | Automatic patch without breaking |
| Git tag | `version: v2.0.1` | Reproducible (same commit for this tag) |
| Git branch | `version: main` | **Not reproducible** (main moves) |
| Commit SHA | `version: abc1234...` | **Maximum** reproducible |

🔍 **Production recommendation**: exact version or commit SHA. Branch
`main` forbidden (risk of silent breaking change on the next install).

## 📚 Exercise 5 — Organization strategy

For a production Ansible repo, organize:

```text
projet/
├── requirements.yml          ← versioned
├── ansible.cfg               ← roles_path = roles:~/.ansible/roles
├── roles/                    ← project-internal roles
├── collections/              ← vendored collections (optional)
├── playbooks/
└── .github/workflows/ci.yml  ← install requirements in CI
```

```ini
# ansible.cfg
[defaults]
roles_path = roles:~/.ansible/roles
collections_path = collections:~/.ansible/collections
```

🔍 **Observation**: `roles_path` prioritizes the project's **internal
roles**, then falls back to the third-party roles installed via
`requirements.yml`.

## 🔍 Observations to note

- **`requirements.yml`** at the project root, **versioned in Git**.
- **Strict pinning** in **production**. `>=` ranges reserved for internal
  libraries or dev.
- **Branch `main`** = NoGo in production (silently breaking).
- **Vendoring** (`-p roles/` + commit) if offline reproducibility is critical.
- **CI**: `ansible-galaxy install -r requirements.yml` as the first step.

## 🤔 Reflection questions

1. You have `version: ">=8.0.0"`. A new version `9.0.0` comes out:
   is it installed if you re-run `ansible-galaxy install`? Why?

2. Difference between `ansible-galaxy install -r requirements.yml` and
   `ansible-galaxy install -r requirements.yml --force`?

3. You want to use the **HEAD** of a Git repo but also be
   reproducible. How do you do it?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`signatures:`** on collections: GPG verification (RHCE 2026).
- **`ANSIBLE_GALAXY_TOKEN`**: auth for private Galaxy.
- **`server_list:`** in `ansible.cfg`: multi-Galaxy (private + public).
- **AAP automation hub**: Red Hat private Galaxy for the enterprise.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/galaxy/installer-roles/
```
