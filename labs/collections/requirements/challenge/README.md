# 🎯 Challenge — Multi-source `requirements.yml`

## ✅ Objective

Write a **`requirements.yml`** that combines **3 different sources**, install it into `local_collections/`, and deposit the list of installed collections on `db1.lab`.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab94-collections.txt` |
| Permissions | `0644`, owner `root` |
| Number of installed collections | **≥ 3** |
| Required sources | Galaxy + Git + (URL **or** dir) |
| Pinning | **Strict** (semver `version: "X.Y.Z"` or Git tag) |

## 🧩 Hints

### Step 1 — `requirements.yml` (to create in `challenge/`)

```yaml
---
collections:
  # Source 1: Galaxy
  - name: ???
    version: ???

  # Source 2: Git (with tag)
  - name: https://github.com/ansible-collections/community.docker.git
    type: ???
    version: ???

  # Source 3: URL or dir (your choice)
  - name: ???
    type: ???
```

### Step 2 — `solution.yml` that orchestrates the installation

```yaml
---
- name: Challenge 94 — installer collections + déposer inventaire
  hosts: db1.lab
  become: true
  gather_facts: false

  tasks:
    - name: Installer les collections du requirements.yml
      ansible.builtin.command:
        cmd: >-
          ansible-galaxy collection install
          -r {{ playbook_dir }}/requirements.yml
          -p {{ playbook_dir }}/../local_collections
        creates: ???              # ← the marker of an already-done install
      delegate_to: localhost
      become: false

    - name: Lister les collections installées localement
      ansible.builtin.command: >-
        ansible-galaxy collection list
        -p {{ playbook_dir }}/../local_collections
      delegate_to: localhost
      become: false
      register: ???
      changed_when: ???

    - name: Déposer le fichier preuve sur db1.lab
      ansible.builtin.copy:
        dest: /tmp/lab94-collections.txt
        content: ???
        owner: ???
        group: ???
        mode: ???
```

### Step 3 — Launch

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

> 💡 **Pitfalls**:
>
> - **`requirements.yml`** (collections) ≠ **`requirements.txt`**
>   (Python). Historical convention: both can coexist in
>   an Ansible project.
> - **Pinning `version:`**: without it, you risk a broken build when the
>   collection bumps to a major (breaking change). Always pin in prod.
> - **`-r requirements.yml`** vs **`collections:`** in `ansible-galaxy
>   install`: the 2nd syntax (YAML key) is modern. Do not mix them.
> - **`signatures:`** on the collections (Ansible 2.13+): GPG
>   verification. Strengthens the supply chain. Format: URLs to a `.sig` file.
> - **`--force` breaks idempotence**: it reinstalls on each pass, so
>   the playbook never converges. And even without it, a collection pulled
>   from a **Git** repo is always reinstalled: galaxy cannot compare
>   a tag to what is already on disk. Hence `creates:` on the command,
>   which really skips the task. Declaring `changed_when: false` would make
>   the idempotence test pass without making anything idempotent: it is the
>   playbook that would be lying.
> - **Internet access required**: this lab installs from `galaxy.ansible.com`
>   **and** clones from GitHub. Offline or behind a closed proxy, it
>   cannot pass: this is assumed, the topic is about external sources.

## 🚀 Launch

```bash
ansible-playbook labs/collections/requirements/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/requirements/challenge/tests/
```

The pytest test validates:

- `/tmp/lab94-collections.txt` exists with mode `0644` and owner `root`.
- At least 3 collections listed in the file.
- At least one collection with an FQCN (dot in the namespace).

## 🧹 Reset

```bash
dsoxlab clean collections-requirements
```

## 💡 Going further

- **GPG signatures**: add `signatures:` to a collection + `--keyring` at launch.
- **Renovate**: configure a bot to auto-bump `version: "X.Y.Z"` on each upstream release.
- **`ansible-lint --profile production`**: zero warning expected.
