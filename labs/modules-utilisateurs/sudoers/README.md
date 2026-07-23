# Lab 43 — `sudoers:` module (manage sudo rights)

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

🔗 [**Ansible sudoers module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-sudoers/)

`community.general.sudoers:` generates files in `/etc/sudoers.d/` with
**automatic validation** via `visudo -cf`. It is the **reference module** to
manage sudo rights idempotently, far safer than a `lineinfile:` on
`/etc/sudoers` (a malformed file locks `sudo` for **all users**).

This module belongs to the **`community.general`** collection: on Ansible Core
2.20, you need `ansible-galaxy collection install community.general`.

Main options: **`name:`** (name of the file in `/etc/sudoers.d/`), **`user:`** or
**`group:`**, **`commands:`**, **`nopassword: true`**, **`state:`**, **`runas:`**,
**`validation:`** (by default `detect` which calls `visudo -cf`).

> ⚠️ **Important about `nopassword:`**: since `community.general` 11.0, the
> default is **`true`** (sudo without password)! To require a password,
> **explicitly** set `nopassword: false`. A classic surprise on recent versions.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** a simple sudo rule via the `sudoers:` module.
2. **Limit** the access to **precise commands** (least privilege principle).
3. **Distinguish** `nopassword: true` (sudo without password) from the default
   (with password).
4. **Manage** rules **on a group** rather than an individual user.
5. **Why** to **never** modify `/etc/sudoers` directly.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install community.general
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/sudoers.d/lab-rhce-*; useradd alice -m 2>/dev/null; useradd bob -m 2>/dev/null; groupadd ops-team 2>/dev/null; true"
```

## 📚 Exercise 1 — Why not `lineinfile:` on `/etc/sudoers`

```yaml
# ❌ DANGEROUS
- ansible.builtin.lineinfile:
    path: /etc/sudoers
    line: "alice ALL=(ALL) NOPASSWD:ALL"
```

🔍 **Risks**:

- If the line is **malformed** (typo, non-standard sudoers syntax),
  `/etc/sudoers` becomes **invalid**.
- `sudo` then refuses to work, **no one** can elevate their rights.
- On a production server, you are **locked out**: impossible to revert without
  physical console or IPMI access.

**With the `sudoers:` module**, the **`visudo -cf %s` validation** is **automatic
and mandatory**, an invalid file is **never** dropped.

## 📚 Exercise 2 — Creating a simple rule

Create `lab.yml`:

```yaml
---
- name: Demo sudoers
  hosts: db1.lab
  become: true
  tasks:
    - name: Donner les droits sudo a alice (avec password)
      community.general.sudoers:
        name: lab-rhce-alice
        user: alice
        commands: ALL
        state: present
```

**Run**:

```bash
ansible-playbook labs/modules-utilisateurs/sudoers/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-alice'
```

🔍 **Observation**: a file `/etc/sudoers.d/lab-rhce-alice` is created:

```text
alice ALL=(ALL) ALL
```

The module has:

- **Validated** the syntax via `visudo -cf` before the drop.
- **Set the right permissions**: `0440` (read for `root` only + `root` group).
  If you try `chmod 0644`, sudo **refuses** the file.

## 📚 Exercise 3 — Sudo without password (`nopassword: true`)

```yaml
- name: Bob peut faire SUDO sans password (DANGER)
  community.general.sudoers:
    name: lab-rhce-bob-nopass
    user: bob
    commands: ALL
    nopassword: true
    state: present
```

**Check the generated file**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-bob-nopass'
```

🔍 **Observation**:

```text
bob ALL=(ALL) NOPASSWD:ALL
```

**`NOPASSWD:`** = sudo without a password prompt.

**Legitimate cases**:

- **Ansible account** on a managed node (`NOPASSWD:ALL` for all modules).
- **CI/CD** account that must run commands without interaction.

**Dangerous cases**: **human users**, an attacker who takes over the user's
account has `root` immediately. To be avoided unless there is a precise technical
reason.

## 📚 Exercise 4 — Limit the commands (least privilege)

```yaml
- name: Alice peut redemarrer chronyd uniquement
  community.general.sudoers:
    name: lab-rhce-alice-chronyd
    user: alice
    commands:
      - /usr/bin/systemctl restart chronyd
      - /usr/bin/systemctl status chronyd
    nopassword: true
    state: present
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-alice-chronyd'
```

```text
alice ALL=(ALL) NOPASSWD:/usr/bin/systemctl restart chronyd, /usr/bin/systemctl status chronyd
```

🔍 **Observation**: alice can **only** run these 2 specific commands via sudo.
`sudo systemctl restart sshd` → **refused**.

**Least privilege pattern**: combine with a dedicated user + restricted SSH keys
(lab 42) → a developer can **only** restart their service without full root access.

## 📚 Exercise 5 — Rules on a **group** rather than a user

```yaml
- name: Tous les membres d ops-team ont sudo
  community.general.sudoers:
    name: lab-rhce-ops-team
    group: ops-team   # Instead of "user:"
    commands: ALL
    state: present
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-ops-team'
```

```text
%ops-team ALL=(ALL) ALL
```

🔍 **Observation**: the **`%`** prefix designates a group in sudoers syntax. All
the users of the `ops-team` group inherit the rights.

**Advantage**: adding a new member = `usermod -aG ops-team carl` →
automatically a sudoer. No need to modify the sudoers file.

## 📚 Exercise 6 — `runas:` (run as...)

By default, `sudo` runs as `root`. `runas:` lets you **force another user** as
the target.

```yaml
- name: Alice peut runner comme deploy uniquement
  community.general.sudoers:
    name: lab-rhce-alice-as-deploy
    user: alice
    runas: deploy
    commands: /opt/myapp/bin/deploy.sh
    nopassword: true
    state: present
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/sudoers.d/lab-rhce-alice-as-deploy'
```

```text
alice ALL=(deploy) NOPASSWD:/opt/myapp/bin/deploy.sh
```

🔍 **Observation**: `(deploy)` requires that the command be run **as `deploy`**,
not root. Alice can do `sudo -u deploy /opt/myapp/bin/deploy.sh`, but **not**
`sudo /opt/myapp/bin/deploy.sh` (which would attempt root → refused).

**Use case**: an operator can restart an app under the application user
**without root escalation**.

## 📚 Exercise 7 — Deletion (`state: absent`)

```yaml
- name: Revoquer les droits sudo de bob
  community.general.sudoers:
    name: lab-rhce-bob-nopass
    state: absent
```

🔍 **Observation**: the **file** `/etc/sudoers.d/lab-rhce-bob-nopass` is deleted.
Bob no longer has sudo rights.

**Important**: the module only touches the file it created (`name:` matches the
filename). The other `/etc/sudoers.d/*` files are not affected.

## 📚 Exercise 8 — The trap: `validate:` disabled

```yaml
# ❌ DANGER
- community.general.sudoers:
    name: lab-rhce-broken
    user: alice
    commands: "INVALID SYNTAX !@#$"
    validation: absent   # Disables visudo -cf
```

🔍 **Observation**: with `validation: absent`, the module **does not validate**
the syntax. The file is dropped as is. If the syntax is invalid, sudo **breaks
globally** (refuses to read `/etc/sudoers.d/*`).

**Absolute rule**: **never disable `validation:`**. The validation is free (a few
ms) and prevents critical incidents.

## 🔍 Observations to note

- **`community.general.sudoers:` module** (not builtin, collection required).
- **Automatic validation** via `visudo -cf`, **always leave it enabled**.
- **Sets the correct permissions** automatically (`0440`).
- **`commands:`** for least privilege (specific commands only).
- **`group:`** for rules on a group (`%` prefix in sudoers syntax).
- **`runas:`** to run as another user (not root by default).
- **`nopassword: true`** = sudo without password, to be reserved for technical /
  CI accounts.
- **Never** modify `/etc/sudoers` directly, always `/etc/sudoers.d/*`.

## 🤔 Reflection questions

1. You want to give developers the right to **restart their app** without giving
   them full sudo. Combine `commands:`, `runas:`, and `nopassword:` for the
   complete scenario.

2. Why is `/etc/sudoers.d/<file>` **safer** than `/etc/sudoers` directly? (hint:
   rule isolation, granularity, rollback).

3. A colleague enables `validation: absent` "because it crashes in CI without
   root access". How do you **actually** solve their problem (without disabling
   the validation)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Defaults pattern**: `Defaults env_keep += "ANSIBLE_*"` to preserve some
  Ansible env variables. To be managed via `template:` on `/etc/sudoers.d/defaults`.
- **`community.general.sudoers: noexec: true`**: prevents the programs run via
  sudo from launching their own sub-shells.
- **Sudo audit**: `journalctl -u sudo` or `/var/log/secure` (RHEL) trace all the
  sudo invocations. Combine with `Defaults log_input,log_output` for a full audit.
- **`!command`** in `commands:`: **forbid** a command even inside an `ALL`.
  E.g. `commands: ['ALL', '!/bin/rm -rf /']` (although this syntax has its
  limits, prefer a whitelist).
- **Lab 40 (`user:`) + Lab 42 (`authorized_key:`) + Lab 43 (`sudoers:`)** = the
  **onboarding trilogy** of a team member.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-utilisateurs/sudoers/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-utilisateurs/sudoers/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-utilisateurs/sudoers/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
