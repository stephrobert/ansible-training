# Lab 32 — `file:` module (states, permissions, symlinks)

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

🔗 [**Ansible file module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-file/)

`ansible.builtin.file:` is the **Swiss army knife of file metadata**. Unlike
`copy:`, it transfers **no content**: it acts only on the **existence**, the
**mode**, the **owner**, the **type** (file, directory, symlink, hardlink). It is
the ideal module to prepare a **tree**, create a **symbolic link** to the current
release, or **remove** an obsolete file.

`file:` stands out with its **`state:`** option, which takes **6 values**: `file`,
`directory`, `absent`, `link`, `hard`, `touch`. Mastering these 6 states covers
95% of the use cases.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Distinguish** the 6 states: `file`, `directory`, `absent`, `link`, `hard`, `touch`.
2. **Create** a multi-level tree with `state: directory`.
3. **Manage** symbolic links (current release, version switching).
4. **Propagate** permissions recursively (`recurse: true`).
5. **Diagnose** a broken symlink (nonexistent target).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "rm -rf /opt/myapp /etc/myapp-old.conf /var/log/myapp-init.timestamp /tmp/lab-file-*"
```

## 📚 Exercise 1 — Create a directory (`state: directory`)

Create `lab.yml`:

```yaml
---
- name: Demo file directory
  hosts: web1.lab
  become: true
  tasks:
    - name: Repertoire de logs applicatifs (avec parents)
      ansible.builtin.file:
        path: /var/log/myapp/archive
        state: directory
        owner: nobody
        group: nobody
        mode: "0750"
```

**Run**:

```bash
ansible-playbook labs/modules-fichiers/file/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'ls -la /var/log/myapp/'
```

🔍 **Observation**: `/var/log/myapp/` AND `/var/log/myapp/archive/` are created
**in a single task**. Ansible automatically creates the parents (equivalent to
`mkdir -p`).

**Idempotence**: 2nd run → `changed=0` (already in the expected state).

**Modification**: change `mode: "0750"` → `mode: "0700"`. Ansible **adjusts** the
mode on both directories.

## 📚 Exercise 2 — Symbolic links (release pattern)

Classic deployment pattern: `/opt/myapp/current` is a **symlink** to the active
release.

```yaml
- name: Creer 2 dossiers de release
  ansible.builtin.file:
    path: "/opt/myapp/releases/{{ item }}"
    state: directory
    mode: "0755"
  loop: [v1.0.0, v1.1.0]

- name: Pointer current vers v1.0.0
  ansible.builtin.file:
    src: /opt/myapp/releases/v1.0.0
    dest: /opt/myapp/current
    state: link
    force: true

- name: Bascule vers v1.1.0 (mise a jour du symlink)
  ansible.builtin.file:
    src: /opt/myapp/releases/v1.1.0
    dest: /opt/myapp/current
    state: link
    force: true
```

🔍 **Observation**: on the 1st run, `current` points to `v1.0.0`. The 2nd task
**switches** the symlink to `v1.1.0` (atomic via `rename`). Classic pattern of
**blue/green deployments**: prepare the new release in `releases/`, switch
`current` at the end.

**`force: true`** is mandatory if `current` already exists (as a file or a
different symlink).

## 📚 Exercise 3 — The broken link pitfall

```yaml
- name: Creer un symlink vers une cible INEXISTANTE
  ansible.builtin.file:
    src: /opt/non-existent-target
    dest: /tmp/lab-file-broken-link
    state: link
    force: true
```

**Run and inspect**:

```bash
ansible-playbook labs/modules-fichiers/file/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'ls -la /tmp/lab-file-broken-link'
```

🔍 **Observation**: the symlink is **created** without an Ansible error, but
**points to nothing**. `ls -la` shows:

```text
lrwxrwxrwx 1 root root 27 ... lab-file-broken-link -> /opt/non-existent-target
```

And `cat lab-file-broken-link` returns `No such file or directory`.

**Solution**: check the target **before** creating the symlink:

```yaml
- name: Verifier que la cible existe
  ansible.builtin.stat:
    path: /opt/myapp/releases/v1.0.0
  register: target_check

- name: Creer symlink seulement si cible OK
  ansible.builtin.file:
    src: /opt/myapp/releases/v1.0.0
    dest: /opt/myapp/current
    state: link
    force: true
  when: target_check.stat.exists and target_check.stat.isdir
```

## 📚 Exercise 4 — Removal (`state: absent`)

```yaml
- name: Nettoyer un fichier obsolete
  ansible.builtin.file:
    path: /etc/myapp-old.conf
    state: absent

- name: Nettoyer un dossier complet (RECURSIF)
  ansible.builtin.file:
    path: /tmp/lab-file-tobeRemoved
    state: absent
```

🔍 **Observation**:

- `state: absent` is **idempotent**: if already absent → `ok` (no error).
- On a **directory**, it is **recursive** (equivalent to `rm -rf`). **Caution!**
- Always **test with `--check --diff`** before `state: absent` on a directory in
  production.

**Defensive pattern**:

```yaml
- name: Stat avant suppression
  ansible.builtin.stat:
    path: /tmp/lab-file-tobeRemoved
  register: dir_stat

- name: Supprimer si existe (avec assertion)
  ansible.builtin.file:
    path: /tmp/lab-file-tobeRemoved
    state: absent
  when: dir_stat.stat.exists and dir_stat.stat.isdir
```

## 📚 Exercise 5 — `recurse: true` (propagate mode/owner)

```yaml
- name: Reparer les permissions sur tout /var/log/myapp
  ansible.builtin.file:
    path: /var/log/myapp
    state: directory
    owner: nobody
    group: nobody
    mode: "0750"
    recurse: true
```

🔍 **Observation**: `recurse: true` propagates `mode/owner/group` to **all files
and subdirectories**. Handy to **repair** broken permissions or homogenize a tree
after a `cp -r` that set everything to `root:root`.

**Performance**: `recurse: true` walks each inode → **slow on large volumes**
(50K files = 30+ seconds). For these cases, prefer a single shell command:

```yaml
- ansible.builtin.command: "chown -R nobody:nobody /var/log/myapp && chmod -R 0750 /var/log/myapp"
  changed_when: false  # ou un test plus fin
```

## 📚 Exercise 6 — `state: touch` (the only non-idempotent one)

```yaml
- name: Creer un timestamp d init
  ansible.builtin.file:
    path: /var/log/myapp-init.timestamp
    state: touch
    mode: "0644"
```

🔍 **Observation**: **`touch` is the only non-idempotent state**, it **always**
changes the mtime, so `changed=1` on every run.

**Legitimate use cases**:

- Init timestamp (created once, updated on every deploy).
- Healthcheck file (a cron that checks the mtime < 5min).

**Cases where `touch` is a bad choice**: creating an empty file you will fill
later, prefer `copy: content: ""` which is **idempotent**.

## 📚 Exercise 7 — The pitfall: `state: file` does not create the file

Unlike `state: directory` which creates the directory, **`state: file` does not
create the file** if it does not exist. It is an **assertion** state: "check that
`path:` is indeed a file (and adjust the perms if so)".

```yaml
# ❌ Ne marche PAS si /tmp/lab-file-test n existe pas
- ansible.builtin.file:
    path: /tmp/lab-file-test
    state: file
    mode: "0644"

# ✅ Pour creer un fichier vide
- ansible.builtin.file:
    path: /tmp/lab-file-test
    state: touch
    mode: "0644"

# ✅ Mieux : copy avec content vide (idempotent)
- ansible.builtin.copy:
    content: ""
    dest: /tmp/lab-file-test
    mode: "0644"
    force: false
```

🔍 **Observation**: `state: file` fails if the file does not exist. To create an
**idempotent** empty file, use `copy: content: "" force: false`.

## 🔍 Observations to note

- **6 states**: `file` / `directory` / `absent` / `link` / `hard` / `touch`.
- **`directory` creates the parents** automatically (`mkdir -p`).
- **`absent` on a directory** is **recursive**, equivalent to `rm -rf`, use with caution.
- **`link` does not check** that the target exists, silent broken symlink.
- **`recurse: true`** propagates mode/owner but **slow** on large volumes.
- **`touch` is the only non-idempotent one**, always `changed=1`.
- **`state: file` does not create** the file, use `touch` or `copy:`.

## 🤔 Reflection questions

1. You have 50,000 files in `/var/log/myapp/` and you want to set them all to
   `mode 0640`. `file: recurse: true` or `command: chmod -R` with
   `changed_when:`? What criteria?

2. You manage a release-based deployment (`/opt/myapp/releases/v1.0.0`,
   `v1.1.0`, etc.) with a `current` symlink. How do you guarantee an **atomic
   switch** with no intermediate state visible to users?

3. Why is `state: touch` **non-idempotent** by design, when all the other
   states are idempotent?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`modification_time:`** + **`access_time:`**: force a precise mtime/atime
  (instead of the now of `touch`). Useful for test cases or cache invalidation.
- **Hardlinks vs symlinks**: `state: hard` shares the inode (the file is deleted
  only when ALL references are removed). Symlink = just a pointer.
- **Lab 31 (`copy:`)**: companion module, metadata **plus** content in one task.
- **Lab 33 (`blockinfile:`)**: modify an existing file without rewriting it.
- **`ansible.posix.acl` module**: to manage POSIX ACLs beyond the basic Unix
  permissions.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-fichiers/file/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-fichiers/file/challenge/solution.yml

# Production profile (the strictest, target RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/file/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a pre-commit
> hook to block any commit that would introduce anti-patterns.
