# 🎯 Challenge — Provision 3 RHCE accounts

## ✅ Objective

On **db1.lab**, create 1 group + 3 user accounts with attributes specific to
each one.

## 🧩 Specifications

### Preliminary group

- `rhce-team`: primary group of the 3 users.

### Users to create

| Name | Shell | Comment | Primary group | Secondary groups | Forced UID | Home |
| --- | --- | --- | --- | --- | --- | --- |
| `alice` | `/bin/bash` | `Alice — admin` | `rhce-team` | `wheel` | (auto) | (default) |
| `bob` | `/bin/bash` | `Bob — dev` | `rhce-team` | — | **2001** | (default) |
| `deploy` | `/bin/bash` | `Compte applicatif deploy` | `rhce-team` | — | **2000** | `/opt/deploy/` |

## 🧩 Stuck?

```bash
dsoxlab hint modules-utilisateurs-user
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧩 Skeleton

```yaml
---
- name: Challenge - 3 comptes RHCE
  hosts: db1.lab
  become: true

  tasks:
    - name: Créer le groupe rhce-team
      ansible.builtin.group:
        name: ???
        state: present

    - name: Créer alice (admin avec sudo wheel)
      ansible.builtin.user:
        name: ???
        comment: ???
        shell: ???
        group: ???
        groups: ???
        append: ???
        state: present

    - name: Créer bob (dev avec UID forcé)
      ansible.builtin.user:
        name: ???
        comment: ???
        shell: ???
        uid: ???
        group: ???
        state: present

    - name: Créer deploy (compte applicatif)
      ansible.builtin.user:
        name: ???
        comment: ???
        shell: ???
        uid: ???
        home: ???
        create_home: ???
        group: ???
        state: present
```

> 💡 **Traps**:
>
> - **UID conflict**: if the UID is already taken (inheritance from a
>   previous lab), `useradd` crashes with "UID is not unique". The `make
>   clean` of the upstream lab must clean it up.
> - **`group:`** vs **`groups:`**: `group` = primary group (a single one),
>   `groups` = secondary groups (list). Classic confusion.
> - **`append: true`** with `groups:`: adds to the existing groups
>   without overwriting them. Without it, the user loses their old groups!
> - **`password:`** must be a **hash** (`crypt('motdepasse', 'sha512')`).
>   Not the plaintext string. For a user without a password: `password: !`
>   (locked) or `password: '*'`.

## 🚀 Run

```bash
ansible-playbook labs/modules-utilisateurs/user/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "id alice bob deploy"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-utilisateurs/user/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-utilisateurs-user
```

## 💡 Going further

- **`generate_ssh_key: true`**: creates an SSH key pair in the user's `~/.ssh/`
  at the time of creation.
- **`password:`**: sets a password (already hashed). Use
  `password: "{{ 'monpassword' | password_hash('sha512') }}"`.
- **`expires:`**: Unix timestamp of the account expiration.
- **Lint**:

   ```bash
   ansible-lint labs/modules-utilisateurs/user/challenge/solution.yml
   ```
