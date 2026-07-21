# Lab 51 — `stat:` module (info on files and folders)

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

🔗 [**Ansible stat module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-stat/)

`ansible.builtin.stat:` returns **information** about a file or folder without
modifying it: existence, type, size, mode, owner, checksum, mtime. It is
**Ansible's number 1 module for conditional logic**: combined with `register:` +
`when:`, it lets you code safe branches.

`stat:` is **read-only** by definition, always `changed=0`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Check the existence** of a file before acting on it.
2. **Distinguish** the types: regular file, folder, symlink, hardlink.
3. **Compare checksums** to detect a modification (`get_checksum: true`).
4. **Measure** the size and the mtime for compliance checks.
5. **Diagnose** a symlink file pointing to nothing.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/lab-stat-*"
```

## 📚 Exercise 1 — File existence

Create `lab.yml`:

```yaml
---
- name: Demo stat
  hosts: db1.lab
  become: true
  tasks:
    - name: Stat sur /etc/passwd
      ansible.builtin.stat:
        path: /etc/passwd
      register: passwd_stat

    - name: Inspecter le resultat
      ansible.builtin.debug:
        var: passwd_stat.stat
```

🔍 **Observation**: `passwd_stat.stat` is a dict that contains:

```yaml
exists: true
isfile: true
isdir: false
islnk: false
size: 1234
mode: '0644'
uid: 0
gid: 0
pw_name: root
gr_name: root
mtime: 1234567890
checksum: <SHA1 of the content>
```

Note: on folders, `isdir: true`. On symlinks, `islnk: true` + `lnk_source`
points to the target.

## 📚 Exercise 2 — Condition on existence (`when:`)

```yaml
- name: Stat sur un fichier optionnel
  ansible.builtin.stat:
    path: /etc/myapp.conf
  register: myapp_conf

- name: Action SI le fichier existe
  ansible.builtin.copy:
    src: /etc/myapp.conf
    dest: /tmp/lab-stat-backup.conf
    remote_src: true
  when: myapp_conf.stat.exists

- name: Action SI le fichier n existe PAS
  ansible.builtin.copy:
    content: "Default config\n"
    dest: /etc/myapp.conf
    mode: "0644"
  when: not myapp_conf.stat.exists
```

🔍 **Observation**: a classic **conditional branch** pattern. Before any
operation on a file that may or may not exist, you stat then decide.

## 📚 Exercise 3 — Distinguish the types

```yaml
- name: Stat sur un dossier
  ansible.builtin.stat:
    path: /etc
  register: etc_stat

- name: Stat sur un symlink (etc/localtime souvent)
  ansible.builtin.stat:
    path: /etc/localtime
  register: localtime_stat

- name: Afficher les types
  ansible.builtin.debug:
    msg: |
      /etc        → exists: {{ etc_stat.stat.exists }}, isdir: {{ etc_stat.stat.isdir }}
      /etc/localtime → exists: {{ localtime_stat.stat.exists }}, islnk: {{ localtime_stat.stat.islnk }}, target: {{ localtime_stat.stat.lnk_source | default('N/A') }}
```

🔍 **Observation**: fields available depending on the type:

| Type | Distinctive fields |
|---|---|
| Regular file | `isfile: true`, `size`, `checksum` |
| Folder | `isdir: true` (no meaningful `size`) |
| Symlink | `islnk: true`, `lnk_source` (target), `lnk_target` (resolved path) |
| Hardlink | `nlink > 1` (number of links) |
| Block/char device | `isblk: true` / `ischr: true` |

## 📚 Exercise 4 — Checksum for modification detection

```yaml
- name: Stat avec checksum
  ansible.builtin.stat:
    path: /etc/passwd
    get_checksum: true
    checksum_algorithm: sha256
  register: passwd_check

- name: Afficher le checksum
  ansible.builtin.debug:
    msg: "SHA256 de /etc/passwd : {{ passwd_check.stat.checksum }}"
```

**Performance warning**: `get_checksum: true` computes the hash by reading the
whole file. On a 1GB file, it is slow. Use it only when you **need** the
checksum (audit, custom idempotence).

**Supported algorithms**: `sha1` (default), `sha256` (recommended), `sha512`,
`md5` (deprecated).

## 📚 Exercise 5 — Mtime and time tests

```yaml
- name: Stat avec mtime
  ansible.builtin.stat:
    path: /etc/passwd
  register: passwd_mtime

- name: Verifier que /etc/passwd n a pas ete modifie depuis 24h
  ansible.builtin.assert:
    that:
      - (ansible_date_time.epoch | int - passwd_mtime.stat.mtime | int) < 86400
    fail_msg: "ALERTE : /etc/passwd modifie depuis moins de 24h"
    success_msg: "OK : /etc/passwd stable depuis 24h+"
```

🔍 **Observation**: `mtime` is a **Unix timestamp** (seconds since 1970). To
compare, subtract and compare in seconds.

**Use case**: security audit, detect recent modifications on sensitive files.

## 📚 Exercise 6 — The trap: broken symlink

```yaml
- name: Creer un symlink vers une cible inexistante
  ansible.builtin.file:
    src: /opt/non-existent
    dest: /tmp/lab-stat-broken-link
    state: link
    force: true

- name: Stat sur le symlink (ne suit PAS le lien par defaut)
  ansible.builtin.stat:
    path: /tmp/lab-stat-broken-link
  register: link_stat

- name: Afficher (le symlink existe mais sa cible n existe pas)
  ansible.builtin.debug:
    msg: |
      exists: {{ link_stat.stat.exists }}
      islnk: {{ link_stat.stat.islnk }}
      lnk_source: {{ link_stat.stat.lnk_source | default('N/A') }}
```

🔍 **Observation**: by default, `stat:` does **not follow** symlinks
(`follow: false`). The symlink itself exists (`exists: true`), but its target
may be absent.

**To follow the link**:

```yaml
- ansible.builtin.stat:
    path: /tmp/lab-stat-broken-link
    follow: true
  register: link_stat_follow
  failed_when: false   # follow + missing target = error otherwise
```

With `follow: true`, `exists: false` if the target does not exist.

## 📚 Exercise 7 — Checksum diff between two files

```yaml
- name: Stat sur le fichier source
  ansible.builtin.stat:
    path: /etc/hosts
    get_checksum: true
  register: src_stat

- name: Stat sur le fichier cible
  ansible.builtin.stat:
    path: /tmp/lab-stat-hosts-copy
    get_checksum: true
  register: dst_stat

- name: Comparer
  ansible.builtin.debug:
    msg: |
      Src checksum : {{ src_stat.stat.checksum }}
      Dst exists : {{ dst_stat.stat.exists }}
      {% if dst_stat.stat.exists %}
      Dst checksum : {{ dst_stat.stat.checksum }}
      Identique : {{ src_stat.stat.checksum == dst_stat.stat.checksum }}
      {% endif %}
```

Useful pattern to **validate** a transfer or detect a **drift** between two
files, without using a `command: diff`.

## 🔍 Observations to note

- **`stat:`** = read-only, always `changed=0`.
- **`register:` then `when: var.stat.exists`** = the base conditional logic
  pattern.
- **`isfile`, `isdir`, `islnk`** = type distinction.
- **`get_checksum: true`** = requires reading the whole file (slow on large files).
- **`follow: false`** (default) = stat on the symlink itself, not on the target.
- **`mtime`** = Unix timestamp, compare to `ansible_date_time.epoch`.

## 🤔 Reflection questions

1. You want to **copy a file only if it has not been modified** locally by the
   user. Which `stat: + checksum + when:` combination?

2. Semantic difference between `stat: follow: true` and `stat: follow: false`,
   when to prefer each?

3. You want to audit **all the setuid binaries** in `/usr/bin/`. Should it be
   `stat:` (with what?) or `find:` (lab 52)? Why?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`get_md5: false`** (default since Ansible 2.x): MD5 is deprecated. Always
  use `sha256`.
- **`get_attributes: false`** (default): lets you retrieve the extended
  attributes (xattr), costly but useful for SELinux audit.
- **`get_mime: false`** (default): MIME-type via `file -i`. Handy for content
  audits.
- **Lab 52 (`find:`)**: for **multi-file** searches by pattern, the `stat:`
  module is not enough (it takes a single `path:`).
- **Lab 53 (`assert:`)**: combine `stat:` + `assert:` for defensive validations
  at the start of a play.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-diagnostic/stat/lab.yml
ansible-lint labs/modules-diagnostic/stat/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/stat/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
