# Lab 52 — `find:` module (multi-file search)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```

## 🧠 Recap

🔗 [**Ansible find module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-find/)

`ansible.builtin.find:` searches for **multiple files** by pattern (glob or regex),
age, size, type. It is the equivalent of the Unix `find` command but with a
**structured** result (a list of dicts) that `loop:` can then consume.

Where `stat:` handles **one file**, `find:` walks through **several**. Typical
RHCE 2026 use cases: clean up old logs (>7 days), list setuid binaries, delete
temporary files larger than 100MB.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Search** by **pattern** (`patterns:` glob or `use_regex: true`).
2. **Filter by age** (`age: 7d`, `age_stamp: mtime`).
3. **Filter by size** (`size: 100m`).
4. **Filter by type** (`file_type: file/directory/link`).
5. **Combine** `find:` + `loop: + file: state: absent` for a targeted cleanup.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -rf /tmp/lab-find-test; mkdir -p /tmp/lab-find-test"
```

## 📚 Exercise 1 — Setup: create test files

```yaml
---
- name: Setup find test
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer 5 fichiers .log de tailles diverses
      ansible.builtin.shell: |
        cd /tmp/lab-find-test
        for n in 1 2 3 4 5; do
          dd if=/dev/zero of=app${n}.log bs=1M count=$((n * 5)) 2>/dev/null
        done
        ls -la /tmp/lab-find-test/
      register: setup_output

    - name: Afficher
      ansible.builtin.debug:
        var: setup_output.stdout_lines
```

🔍 **Observation**: 5 files `app1.log` (5M) to `app5.log` (25M).

## 📚 Exercise 2 — Search by pattern (glob)

```yaml
- name: Trouver tous les .log
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    patterns: '*.log'
  register: log_files

- name: Afficher la liste
  ansible.builtin.debug:
    msg: "{{ log_files.files | map(attribute='path') | list }}"
```

🔍 **Observation**: `log_files.files` is a **list of dicts** (one per file found)
with: `path`, `size`, `mode`, `mtime`, `uid`, `gid`, etc., like a `stat:` per file.

**Useful register fields**:

- **`log_files.files`**: list of files found (dicts).
- **`log_files.matched`**: total number found.
- **`log_files.examined`**: number of files scanned before filtering.

## 📚 Exercise 3 — Filter by size

```yaml
- name: Trouver les .log de plus de 10Mo
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    patterns: '*.log'
    size: 10m
  register: big_logs

- name: Afficher
  ansible.builtin.debug:
    msg: "Gros logs : {{ big_logs.files | map(attribute='path') | list }}"
    # → app3.log (15M), app4.log (20M), app5.log (25M)
```

**`size:` format**:

- **`10m`** = at least 10 megabytes (no prefix = `>= 10m`).
- **`-100k`** = less than 100 kilobytes (`-` prefix only).
- **`1g`** = at least 1 gigabyte.
- Suffixes: `b` (bytes), `k`, `m`, `g`, `t`.

> ⚠️ **No `+` prefix** like with the Unix `find` command: Ansible rejects
> `+10m`. No prefix = greater than or equal.

## 📚 Exercise 4 — Filter by age

```yaml
- name: Trouver les fichiers modifies depuis plus de 7 jours
  ansible.builtin.find:
    paths: /var/log
    patterns: '*.log'
    age: 7d
  register: old_logs

- name: Trouver les fichiers tres recents (< 1h)
  ansible.builtin.find:
    paths: /var/log
    patterns: '*.log'
    age: -1h
  register: recent_logs
```

**`age:` format**:

- **`7d`** = 7 days or more (by default based on `mtime`).
- **`-1h`** = less than 1 hour (`-` sign = less than).
- Suffixes: `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks).

**`age_stamp:`**: choose the timestamp to compare.

- **`mtime`** (default): last modification.
- **`atime`**: last access.
- **`ctime`**: last metadata change.

## 📚 Exercise 5 — Filter by type

```yaml
- name: Trouver tous les dossiers
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    file_type: directory
  register: dirs

- name: Trouver les symlinks
  ansible.builtin.find:
    paths: /etc
    file_type: link
    recurse: false
  register: symlinks
```

**`file_type:` values**: `file` (default), `directory`, `link`, `any`.

## 📚 Exercise 6 — `recurse: true` (recursive descent)

```yaml
- name: Trouver TOUS les .conf dans /etc et sous-dossiers
  ansible.builtin.find:
    paths: /etc
    patterns: '*.conf'
    recurse: true
  register: all_conf

- name: Compter
  ansible.builtin.debug:
    msg: "{{ all_conf.matched }} fichiers .conf trouves dans /etc/"
```

🔍 **Observation**: without `recurse: true`, `find:` only looks at **`/etc/*.conf`**.
With it, it descends into `/etc/sysconfig/`, `/etc/sysctl.d/`, etc.

**Performance**: `recurse: true` on `/` can take hours on a loaded system.
**Always** scope with a precise `paths:`.

## 📚 Exercise 7 — `find:` + automatic cleanup

Classic pattern: **delete** all the files matching a pattern.

```yaml
- name: Trouver les .log > 1Mo et plus de 0 jours
  ansible.builtin.find:
    paths: /tmp/lab-find-test
    patterns: '*.log'
    size: 1m
  register: logs_to_clean

- name: Supprimer ces fichiers
  ansible.builtin.file:
    path: "{{ item.path }}"
    state: absent
  loop: "{{ logs_to_clean.files }}"
  loop_control:
    label: "{{ item.path }}"
```

🔍 **Observation**: the `find` + `loop: + file: state: absent` pattern. Idempotent
(a 2nd run finds 0 files → `loop:` 0 iterations).

**Shell alternative**: `find /tmp/lab-find-test -name '*.log' -size +1M -delete`.
Less readable, less idempotent, but faster on **large volumes**.

## 📚 Exercise 8 — The trap: `find:` on a slow NFS partition

```yaml
- name: Find sur NFS (lent)
  ansible.builtin.find:
    paths: /mnt/nfs-data
    patterns: '*.dump'
    recurse: true
  register: nfs_dumps
  timeout: 60   # Kill after 60s
```

🔍 **Observation**: on a slow NFS or a very large FS, `find:` can block the play.
**`timeout:`** at the task level limits the duration.

**Mitigation**:

- **Scope** by a precise subfolder (not `/`).
- **Limit** the depth via `depth:` (Ansible 2.10+, otherwise shell).

## 🔍 Observations to note

- **`find:`** returns `<reg>.files` (list of dicts) + `<reg>.matched` (count).
- **`patterns:`** = glob by default, `use_regex: true` for Python regex.
- **`size: 10m`** / **`age: 7d`** = standard filters.
- **`recurse: true`** = recursive descent (mind the performance).
- **`file_type:`**: `file` / `directory` / `link` / `any`.
- **`find + loop + file: state: absent` pattern** = idempotent cleanup.

## 🤔 Reflection questions

1. You want to **archive** all the `.log` older than 7 days into
   `/var/backups/` before deleting them. Full pipeline (modules + order)?

2. Difference between `patterns: '*.log'` (glob) and `patterns: '\\.log$'` with
   `use_regex: true`?

3. On 100 hosts, a recursive `find:` on `/var/log/` takes 30s per host. How do
   you **parallelize** without saturating?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`get_checksum: true`**: computes the hash of each file found. Slow but
  useful for audit.
- **`hidden: true`**: includes `.<dotfile>` files. Disabled by default.
- **`excludes:`**: list of patterns to **exclude** from the result.
- **`depth:`**: maximum depth (Ansible 2.10+), useful on deep trees.
- **Lab 51 (`stat:`)** = stat on **one** file; **Lab 52 (`find:`)** = on several.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-diagnostic/find/lab.yml
ansible-lint labs/modules-diagnostic/find/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/find/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
