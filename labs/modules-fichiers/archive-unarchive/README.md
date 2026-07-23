# Lab 35 — `archive:` and `unarchive:` modules (compress and extract)

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

🔗 [**Ansible archive and unarchive modules**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/archive-unarchive/)

Two complementary modules to manage **tarballs** and **zips**:

- **`archive:`** creates an archive (`.tar.gz`, `.zip`, etc.) **on the managed node**
  from one or more paths.
- **`unarchive:`** extracts an archive to a directory: from the control node
  (auto-copy), a URL, or an archive already on the managed node (`remote_src: true`).

Typical use cases: **backup before migration** (archiving a `/etc/myapp/`),
**application deployment** from a tarball stored on S3, **restoration** of a
compressed SQL dump.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** a `.tar.gz` archive on the managed node with `archive:`.
2. **Distinguish** the 3 modes of `unarchive:` (auto-copy, URL, `remote_src`).
3. **Make** `unarchive:` idempotent with `creates:`.
4. **Identify** the **trailing slash** pitfall on `archive: path:`.
5. **Use** `extra_opts: --strip-components=1` for upstream archives.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -rf /opt/data-source /opt/backup /opt/restored"
```

## 📚 Exercise 1 — `archive:` basics

Create `lab.yml`:

```yaml
---
- name: Demo archive
  hosts: db1.lab
  become: true
  tasks:
    - name: Repertoire source
      ansible.builtin.file:
        path: /opt/data-source
        state: directory
        mode: "0755"

    - name: Fichiers de donnees
      ansible.builtin.copy:
        content: "Donnee {{ item }}\n"
        dest: "/opt/data-source/file{{ item }}.txt"
        mode: "0644"
      loop: [1, 2, 3]

    - name: Repertoire pour l archive
      ansible.builtin.file:
        path: /opt/backup
        state: directory
        mode: "0755"

    - name: Creer l archive
      ansible.builtin.archive:
        path: /opt/data-source/
        dest: /opt/backup/data.tar.gz
        format: gz
```

**Run and inspect**:

```bash
ansible-playbook labs/modules-fichiers/archive-unarchive/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'ls -la /opt/backup/ && tar tzf /opt/backup/data.tar.gz'
```

🔍 **Observation**: the archive contains `file1.txt`, `file2.txt`, `file3.txt`
**at the root level** (not inside `data-source/`). This is the effect of the
**trailing slash** on `path: /opt/data-source/`.

## 📚 Exercise 2 — The trailing slash pitfall

```yaml
- name: Sans slash final - inclut le dossier parent
  ansible.builtin.archive:
    path: /opt/data-source
    dest: /opt/backup/data-with-parent.tar.gz
    format: gz

- name: Avec slash final - inclut le contenu directement
  ansible.builtin.archive:
    path: /opt/data-source/
    dest: /opt/backup/data-flat.tar.gz
    format: gz
```

**Compare**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'tar tzf /opt/backup/data-with-parent.tar.gz'
# data-source/file1.txt
# data-source/file2.txt
# data-source/file3.txt

ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'tar tzf /opt/backup/data-flat.tar.gz'
# file1.txt
# file2.txt
# file3.txt
```

🔍 **Observation**: with a slash → **flat** content. Without a slash → content
**under the source directory**. This changes the structure at extraction. **Always
check with `tar tzf`** before deploying.

## 📚 Exercise 3 — `unarchive:` auto-copy mode (local `src:`)

```yaml
- name: Repertoire pour extraction
  ansible.builtin.file:
    path: /opt/restored
    state: directory
    mode: "0755"

- name: Extraire (depuis archive sur le managed node, deja generee)
  ansible.builtin.unarchive:
    src: /opt/backup/data.tar.gz
    dest: /opt/restored
    remote_src: true
    creates: /opt/restored/file1.txt
```

🔍 **Observation**:

- **`remote_src: true`**: Ansible looks for `src:` on the managed node side (not the control side).
- **`creates: /opt/restored/file1.txt`**: if this file exists → task **skipped**.
  Idempotence guaranteed.

**Run twice**: first time `changed=1`, second time `ok` (skipped thanks to `creates:`).

## 📚 Exercise 4 — `unarchive:` remote URL mode

```yaml
- name: Telecharger et extraire (sans passer par le control node)
  ansible.builtin.unarchive:
    src: https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
    dest: /opt/
    remote_src: true
    creates: /opt/node_exporter-1.7.0.linux-amd64/node_exporter
    extra_opts:
      - "--strip-components=0"
```

🔍 **Observation**: Ansible **downloads directly onto the managed node**
(no download on the control node plus SSH transfer). More efficient for large
tarballs.

**`extra_opts: ["--strip-components=N"]`**: removes the first N levels of the
tree. Classic trick: with the upstream `archive-X.Y.Z/...` convention
→ `--strip-components=1` to extract directly into `dest:` without the parent
directory.

## 📚 Exercise 5 — `unarchive:` classic mode (auto-copy from files/)

```yaml
- name: Extraire un tarball stocke localement (auto-copy)
  ansible.builtin.unarchive:
    src: files/myapp-1.0.tar.gz
    dest: /opt/myapp
    creates: /opt/myapp/bin/myapp
```

🔍 **Observation**: without `remote_src: true`, Ansible **transfers** the tarball
from `files/` (on the control node side) to the managed node, then extracts it.

**When to prefer this approach**: tarballs versioned in the Ansible repo
(version controlled, no dependency on the internet).

**Differences between the 3 modes**:

| Mode | Source | Transfer |
|---|---|---|
| auto-copy (default) | Control node (`files/`) | SSH to managed |
| URL (`remote_src: true`) | HTTP(S) URL | Direct to managed (without control) |
| Local (`remote_src: true`) | Managed node | No transfer (already there) |

## 📚 Exercise 6 — `archive:` with exclusions

```yaml
- name: Archiver /var/log avec exclusions
  ansible.builtin.archive:
    path: /var/log
    dest: /opt/backup/logs.tar.gz
    format: gz
    exclude_path:
      - /var/log/journal
      - /var/log/btmp
      - /var/log/wtmp
```

🔍 **Observation**: `exclude_path:` accepts a list of paths to **exclude** from
the archive. Handy to avoid bundling binary system log files or large useless
files.

## 📚 Exercise 7 — The pitfall: `creates:` on the wrong file

```yaml
# ❌ Wrong: creates never matches → extracts on every run
- ansible.builtin.unarchive:
    src: /opt/backup/data.tar.gz
    dest: /opt/restored
    remote_src: true
    creates: /opt/restored/binary-qui-n-existe-pas

# ✅ Good: creates points to a real file after extraction
- ansible.builtin.unarchive:
    src: /opt/backup/data.tar.gz
    dest: /opt/restored
    remote_src: true
    creates: /opt/restored/file1.txt
```

🔍 **Observation**: `creates:` must point to a **file that will exist after
extraction**. If the referenced file never appears (not in the archive or wrong
path), `unarchive:` extracts **on every run** → loss of idempotence.

**Best practice**: use a **version marker file** (`/opt/myapp/VERSION`,
`/opt/myapp/.installed`) that contains the installed version number.

## 🔍 Observations to note

- **`archive:`** creates tarballs (`gz`, `bz2`, `xz`, `zip`).
- **`unarchive:`** has **3 modes**: auto-copy (default), URL (`remote_src: true`), local-to-managed (`remote_src: true`).
- **`creates:`** is mandatory to make `unarchive:` idempotent.
- **Trailing slash on `archive: path:`** changes the archive structure: always `tar tzf` before deploying.
- **`extra_opts: ["--strip-components=1"]`** = pattern to strip the root directory of an upstream archive.
- **`exclude_path:`** on `archive:` to avoid large or irrelevant files.

## 🤔 Reflection questions

1. You deploy node_exporter v1.7.0 from upstream. The archive contains
   `node_exporter-1.7.0.linux-amd64/node_exporter`. Which `--strip-components:` and
   which `dest:` to get `/opt/node_exporter/node_exporter` directly?

2. You want to **pull back** `/var/log` from db1 to the control node. Which
   pipeline: `archive:` + `fetch:`, or directly `synchronize:` (rsync)?

3. Why must `creates:` reference a **specific file** rather than `dest:` itself
   (which always exists after the 1st run)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`archive: format: xz`**: more efficient compression than `gz` (~30% gain)
  but slower. For cold backups.
- **`archive: remove: true`**: removes the sources after archiving. Log rotation
  pattern: archive then delete the original content.
- **`unarchive: list_files: true`**: returns the **list of files** in
  `register:` without extracting. For audit or prior verification.
- **`synchronize:`** (ansible.posix collection): rsync wrapper, an alternative
  for massive transfers with delta, not idempotent by default, more complex.
- **Lab 31 (`copy:`)** + **Lab 34 (`fetch:`)**: simple transfer modules
  (one file).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-fichiers/archive-unarchive/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-fichiers/archive-unarchive/challenge/solution.yml

# Production profile (the strictest, target RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/archive-unarchive/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a pre-commit
> hook to block any commit that would introduce anti-patterns.
