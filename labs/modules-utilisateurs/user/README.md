# Lab 40 — `user:` module (create, modify, delete users)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**Ansible user module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-user/)

`ansible.builtin.user:` manages **Linux users**: creation, modification of the
attributes (shell, home, groups), deletion, password hashing, default SSH key
management. It is the number 1 module for **account management** on the managed
nodes.

Critical RHCE 2026 options: **`name:`**, **`state:`**, **`shell:`**,
**`groups:`** + **`append:`**, **`password:`** (with `password_hash`),
**`uid:`**, **`comment:`**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** a user with home, shell, secondary groups.
2. **Hash** a password with `password_hash('sha512')` for `password:`.
3. **Distinguish** `groups: + append: true` (add) vs `groups:` alone (replace).
4. **Force** a precise `uid:` for system accounts.
5. **Delete** an account with `remove: true` (also removes the home).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "for u in alice bob charlie deploy; do userdel -rf \$u 2>/dev/null; done; true"
```

## 📚 Exercise 1 — Basic creation

Create `lab.yml`:

```yaml
---
- name: Demo user simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer alice
      ansible.builtin.user:
        name: alice
        comment: "Alice — admin RHCE 2026"
        shell: /bin/bash
        state: present

    - name: Verifier la creation
      ansible.builtin.command: id alice
      register: alice_id
      changed_when: false

    - name: Afficher l UID
      ansible.builtin.debug:
        var: alice_id.stdout
```

**Run**:

```bash
ansible-playbook labs/modules-utilisateurs/user/lab.yml
```

🔍 **Observation**:

- First run: `changed=1`, `useradd alice` executed.
- Second run: `changed=0`, alice already exists with the right attributes.
- The UID is **auto-assigned** (first free one ≥ 1000).
- The **home `/home/alice/`** is created by default, the **primary group
  `alice`** is created automatically.

## 📚 Exercise 2 — Secondary groups: `append: true` vs without

```yaml
- name: Creer bob avec wheel + docker (sans append)
  ansible.builtin.user:
    name: bob
    shell: /bin/bash
    groups: [wheel, docker]
    append: false  # Default

- name: Modifier bob — ajouter video (avec append)
  ansible.builtin.user:
    name: bob
    groups: [video]
    append: true   # Adds, without touching the others
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'id bob'
```

🔍 **Observation**: `bob` is in `wheel`, `docker`, **and** `video`. Without
`append: true`, the second task would have **replaced** the groups, bob would
have lost `wheel` and `docker`.

**Absolute rule**: to modify the groups of an existing user, **always
`append: true`** unless you explicitly want to **reset** the list.

## 📚 Exercise 3 — Hashed password

Critical case: you **never store** a plaintext password in a playbook.

```yaml
- name: Creer charlie avec password
  ansible.builtin.user:
    name: charlie
    shell: /bin/bash
    password: "{{ 'PasswordEnClair2026' | password_hash('sha512') }}"
    update_password: on_create  # Does not change the password if the user already exists
```

🔍 **Observation**:

- `password_hash('sha512')` generates a hash compatible with `/etc/shadow`.
- **Without a fixed salt**, the hash differs at each run → the task is **always
  `changed`** (loss of idempotence).
- **`update_password: on_create`** = only touches the password **if the user is
  created** (not if it already exists). Allows the initial creation **without**
  modifying the password at each run.

**Clean RHCE pattern**:

```yaml
# Store the hash in host_vars (with Vault)
# host_vars/db1.lab.yml:
charlie_password_hash: "$6$randomsalt$hashvalue..."

# In the playbook:
- ansible.builtin.user:
    name: charlie
    password: "{{ charlie_password_hash }}"
```

The hash is generated **once** (`mkpasswd -m sha-512`) and stored in Vault.

## 📚 Exercise 4 — Forced UID and GID (system accounts)

For **system** or **application** accounts, you often fix the UID/GID so that
they are **identical on all hosts** (NFS, file sharing).

```yaml
- name: Creer deploy avec UID 2000 (compte applicatif)
  ansible.builtin.user:
    name: deploy
    uid: 2000
    group: deploy   # Primary group
    shell: /bin/bash
    home: /opt/deploy
    create_home: true
    system: false
```

🔍 **Observation**:

- **`uid: 2000`** forces the UID. If the UID is already taken by another user,
  the task is **failed**.
- **`group:`** specifies the primary group (created via the separate `group:`
  module if necessary, see lab 41).
- **`home:`** forces the home (`/opt/deploy` instead of `/home/deploy`).
- **`system: true`** creates a system user (UID < 1000, no home by default).

## 📚 Exercise 5 — Modifying an existing user

```yaml
- name: Modifier le shell de alice (zsh → bash)
  ansible.builtin.user:
    name: alice
    shell: /bin/zsh

- name: Verifier
  ansible.builtin.command: getent passwd alice
  register: alice_passwd
  changed_when: false

- ansible.builtin.debug:
    var: alice_passwd.stdout
    # → alice:x:1001:1001:...:/home/alice:/bin/zsh
```

🔍 **Observation**: the module **detects** that the shell has changed and runs
`usermod -s /bin/zsh alice`. Idempotent: 2nd run → `ok`.

**All the attributes can be modified**: `comment`, `shell`, `home`, `groups`,
`uid`, `gid`. Except `name` (the name is the identification **key**).

## 📚 Exercise 6 — Deletion (`state: absent`)

```yaml
- name: Supprimer charlie SANS son home
  ansible.builtin.user:
    name: charlie
    state: absent
    remove: false  # Default

- name: Supprimer alice ET son home
  ansible.builtin.user:
    name: alice
    state: absent
    remove: true
```

🔍 **Observation**:

- **`remove: false`** (default) = `userdel charlie` → home `/home/charlie/`
  **kept**.
- **`remove: true`** = `userdel -r alice` → home + mail spool **deleted**.

**Audit trail**: `remove: false` is the **safe** default, you can recover the
files of a deleted user. `remove: true` is for the **final cleanup**.

## 📚 Exercise 7 — The trap: `groups:` that erases everything

```yaml
# ❌ DANGER: erases bob's existing groups
- ansible.builtin.user:
    name: bob
    groups: [wheel]
    # No append: true → REPLACES
```

🔍 **Observation**: if bob was already in `[wheel, docker, video]`, after this
task bob is **only in `wheel`**. Bob lost `docker` and `video`.

**Mitigation**: **always** add `append: true` when modifying:

```yaml
- ansible.builtin.user:
    name: bob
    groups: [wheel]
    append: true  # ✅ Adds if not already in, removes nothing
```

**Case where `append: false` is legitimate**: when you intentionally **reset**
the list of groups (offboarding, rights downgrade).

## 🔍 Observations to note

- **`name:`** = identification key, **never** modify it.
- **`groups: + append: true`** to ADD to the existing groups.
- **`password:`** = SHA-512 hash (use `| password_hash('sha512')`).
- **`update_password: on_create`** to avoid overwriting the password at each run.
- **`uid:`** forced for system / application accounts (multi-host consistency).
- **`remove: true`** on `state: absent` also removes the home.
- **Idempotence**: all the attributes are checked and adjusted if necessary.

## 🤔 Reflection questions

1. You want to create 50 users with their respective SSH keys. Which pattern
   (`loop:`, `subelements`, `with_items`)? How do you articulate `user:` and
   `authorized_key:` (lab 42)?

2. Why does `password_hash('sha512')` **without a fixed salt** break idempotence?
   What is the **clean** solution without a hardcoded hash in the repo?

3. A colleague suggests **deleting a user** with `command: userdel -r`. What are
   the **3 advantages** of `user: state: absent: remove: true`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`generate_ssh_key: true`**: generate an SSH pair (private+public) at the
  time of the user's creation. Handy for application accounts.
- **`expires:`**: account expiration date (Unix timestamp). Useful for temporary
  accounts (interns, external audit).
- **`password_lock: true`**: lock the account (`usermod -L`) without deleting it.
  Login via password disabled, but SSH keys still work.
- **`users +keys` pattern**: combination of `user:` + `authorized_key:` (lab 42)
  via `subelements`. See lab 21.
- **`getent:` module**: retrieve a user's/group's info from NSS (LDAP, AD, NIS)
  without depending on the local `/etc/passwd`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-utilisateurs/user/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-utilisateurs/user/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-utilisateurs/user/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
