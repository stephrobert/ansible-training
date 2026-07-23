# Lab 42 — `authorized_key:` module (users' SSH keys)

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

🔗 [**Ansible authorized_key module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-authorized-key/)

`ansible.posix.authorized_key:` manages the **public SSH keys** in a user's
`~/.ssh/authorized_keys` file. It is the tool for **provisioning SSH access**:
add, remove, or **force the exclusive list** of authorized keys.

This module belongs to the **`ansible.posix`** collection (not builtin): on
Ansible Core 2.20, you need `ansible-galaxy collection install ansible.posix`.

Main options: **`user:`**, **`key:`**, **`state:`**, **`exclusive: true`**
(replaces all existing keys), **`comment:`**, **`key_options:`**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Add** an SSH key to an existing user.
2. **Distinguish** `state: present` (add) from `exclusive: true` (replace).
3. **Restrict** a key with `key_options:` (`from=`, `command=`, `no-pty`).
4. **Load** a key from a local file (`lookup('file', ...)`).
5. **Provision** several keys for several users in a single pass with
   `subelements`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install ansible.posix
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "for u in alice bob; do userdel -rf \$u 2>/dev/null; useradd \$u -m; done; true"
mkdir -p labs/modules-utilisateurs/authorized-key/files
```

Generate a test SSH key (local):

```bash
ssh-keygen -t ed25519 -f labs/modules-utilisateurs/authorized-key/files/alice.pub.key -N "" -C "alice@laptop"
ssh-keygen -t ed25519 -f labs/modules-utilisateurs/authorized-key/files/bob.pub.key -N "" -C "bob@laptop"
```

(We use `.pub.key` to retrieve the **public key** without the `_rsa`/`_ed25519`
that could be confused with an SSH config file.)

## 📚 Exercise 1 — Add a key to a user

Create `lab.yml`:

```yaml
---
- name: Demo authorized_key
  hosts: db1.lab
  become: true
  tasks:
    - name: Ajouter la cle d alice
      ansible.posix.authorized_key:
        user: alice
        key: "{{ lookup('file', 'files/alice.pub.key.pub') }}"
        state: present
```

**Run**:

```bash
ansible-playbook labs/modules-utilisateurs/authorized-key/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /home/alice/.ssh/authorized_keys'
```

🔍 **Observation**:

- 1st run: `changed=1`, creation of `/home/alice/.ssh/` with mode `0700` and of
  `authorized_keys` with mode `0600` (Ansible respects the strict SSH permissions).
- 2nd run: `changed=0`, the key is already present.

**`file` lookup**: Ansible **reads** the local file on the control node and
**injects** its content as a string. The key is **not transferred** as a file,
it is just its content that is added to `authorized_keys`.

## 📚 Exercise 2 — `exclusive: true` (full replacement)

```yaml
- name: Pre-creer une cle "manuelle" dans authorized_keys
  ansible.builtin.lineinfile:
    path: /home/alice/.ssh/authorized_keys
    line: "ssh-rsa AAAAOLD-MANUAL-KEY old@laptop"
    create: true
    owner: alice
    group: alice
    mode: "0600"

- name: Forcer la liste exclusive (efface l ancienne cle)
  ansible.posix.authorized_key:
    user: alice
    key: "{{ lookup('file', 'files/alice.pub.key.pub') }}"
    state: present
    exclusive: true
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /home/alice/.ssh/authorized_keys'
```

🔍 **Observation**: only the new key is present. **`exclusive: true`** **erases**
all existing keys to leave only the specified ones.

**Use case**: mass access revoke (a developer leaves the team → rerun the play
without their key to revoke it everywhere).

**Risk**: if `key:` is empty or the lookup fails, **all the keys are erased**.
To be used with a prior `assert:`.

## 📚 Exercise 3 — `key_options:` (key restrictions)

```yaml
- name: Cle restreinte (from=IP + commande forcee)
  ansible.posix.authorized_key:
    user: bob
    key: "{{ lookup('file', 'files/bob.pub.key.pub') }}"
    state: present
    key_options: 'from="10.10.20.0/24",command="/usr/local/bin/restricted-cmd",no-pty,no-X11-forwarding'
```

🔍 **Observation**: the line in `authorized_keys` is prefixed by the restrictions:

```text
from="10.10.20.0/24",command="/usr/local/bin/restricted-cmd",no-pty,no-X11-forwarding ssh-ed25519 AAAA... bob@laptop
```

**Common restrictions**:

| Option | Effect |
|---|---|
| `from="IP_or_CIDR"` | Limits the allowed source IP |
| `command="/path"` | Forces the execution of this command (ignores the client SSH command) |
| `no-pty` | No TTY (forbids interactive `ssh user@host`) |
| `no-X11-forwarding` | No X11 forwarding |
| `no-port-forwarding` | No SSH tunnel (`-L`, `-R`) |
| `no-agent-forwarding` | No SSH agent forwarding |

**Security-hardened pattern**: `from="" + command="" + no-pty + no-X11 + no-port`
for **service keys** (rsync, backup, monitoring): an attacker who steals the key
can do **nothing** other than the enforced command.

## 📚 Exercise 4 — Multi-user pattern with `subelements`

```yaml
- name: Demo provisioning multi-users
  hosts: db1.lab
  become: true
  vars:
    team_users:
      - name: alice
        ssh_keys:
          - "ssh-ed25519 AAAA1 alice@laptop"
          - "ssh-ed25519 AAAA2 alice@server"
      - name: bob
        ssh_keys:
          - "ssh-ed25519 BBBB1 bob@laptop"
  tasks:
    - name: Ajouter chaque cle a chaque user (subelements)
      ansible.posix.authorized_key:
        user: "{{ item.0.name }}"
        key: "{{ item.1 }}"
        state: present
      loop: "{{ team_users | subelements('ssh_keys') }}"
      loop_control:
        label: "{{ item.0.name }} key {{ item.1[0:30] }}..."
```

🔍 **Observation**: `subelements` produces `(parent, child)` pairs, perfect for
**N users with M keys each**. A single task, idempotent.

See lab 21 (with_subelements legacy) for the migration from the old syntax.

## 📚 Exercise 5 — Removing a key (`state: absent`)

```yaml
- name: Revoquer la cle d alice
  ansible.posix.authorized_key:
    user: alice
    key: "{{ lookup('file', 'files/alice.pub.key.pub') }}"
    state: absent
```

🔍 **Observation**: Ansible matches **by key content** (not by comment nor by
hash). If you generate a new key, the old one remains.

**Full revoke pattern**: `state: absent` + `key: "{{ old_key }}"`. If you have
several keys to revoke, either `loop:` over the keys to remove, or
`exclusive: true` with the final list.

## 📚 Exercise 6 — Load the keys from a folder (`*.pub`)

Real pattern: every developer drops their public key into
`files/users/<username>.pub`. The playbook loads them automatically.

```yaml
- name: Recuperer la liste des fichiers .pub
  ansible.builtin.find:
    paths: "{{ inventory_dir }}/../files/users"
    patterns: '*.pub'
  delegate_to: localhost
  register: pub_keys

- name: Provisionner chaque user avec sa cle
  ansible.posix.authorized_key:
    user: "{{ item.path | basename | regex_replace('\\.pub$', '') }}"
    key: "{{ lookup('file', item.path) }}"
    state: present
  loop: "{{ pub_keys.files }}"
  loop_control:
    label: "{{ item.path | basename }}"
```

🔍 **Observation**: Ansible **derives** the username from the file name
(`alice.pub` → user `alice`). Adding a new key = just drop `carl.pub` in the
folder, no need to modify the playbook.

## 📚 Exercise 7 — The trap: strict SSH permissions

If you create `~/.ssh/authorized_keys` **manually** (or via `copy:`) with
permissions that are too open, **SSH refuses** the key.

```yaml
# ❌ Bad: no strict mode
- ansible.builtin.copy:
    content: "ssh-ed25519 AAAA... alice@laptop\n"
    dest: /home/alice/.ssh/authorized_keys
    owner: alice
    group: alice
    # Default mode: 0644 → SSH REFUSES

# ✅ Good
- ansible.builtin.copy:
    content: "ssh-ed25519 AAAA... alice@laptop\n"
    dest: /home/alice/.ssh/authorized_keys
    owner: alice
    group: alice
    mode: "0600"
```

🔍 **Observation**: `~/.ssh/` must be **`0700`**, `~/.ssh/authorized_keys`
**`0600`**. Otherwise `sshd` refuses silently (logs `Authentication refused: bad
ownership or modes`). **`authorized_key:`** handles this automatically, one of
the reasons to **prefer this module to a raw `copy:`**.

## 🔍 Observations to note

- **`ansible.posix.authorized_key:` module** (not builtin, collection required).
- **`exclusive: true`** = replaces all keys (useful for mass revoke).
- **`key_options:`** = SSH restrictions (`from=`, `command=`, `no-pty`).
- **`lookup('file', ...)`** = load the key from a local file (control node).
- **`subelements` pattern** = N users × M keys in a single task.
- **`authorized_key:`** automatically handles the **strict SSH permissions**
  (700/600).

## 🤔 Reflection questions

1. You want to **revoke** the key of a developer who leaves the team on 100
   servers. Which pattern: `state: absent` + exact key, or `exclusive: true`
   with the final list? Advantages of each?

2. You give a **backup key** to an external script. How do you restrict it so
   that it can **only** run `/usr/local/bin/backup.sh`? (combination of
   `key_options:`).

3. You have 50 developers and 10 servers. Should it be **`loop:` over the users**
   or **`loop:` over the servers**? (hint: `subelements` + `delegate_to`).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`manage_dir: false`**: do not create `~/.ssh/` automatically. To be used if
  the home is on NFS or a shared FS that must manage its own permissions.
- **`path:`**: force a custom path instead of `~/.ssh/authorized_keys`. For
  cases where SSH looks for the keys elsewhere (custom sshd config).
- **`validate_certs:`**: for keys from HTTPS URLs, TLS verification of the server.
- **`git pull` + deployed key pattern**: the key provided by the module serves
  an automated git pull. Combine with `key_options: command="git-shell -c"`.
- **Lab 43 (sudoers)**: complement the SSH keys with the sudo rights.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-utilisateurs/authorized-key/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-utilisateurs/authorized-key/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-utilisateurs/authorized-key/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
