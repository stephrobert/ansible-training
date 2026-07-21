# Lab 33 — `blockinfile:` module (idempotent multi-line block)

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

🔗 [**Ansible blockinfile module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-blockinfile/)

`ansible.builtin.blockinfile:` inserts or updates a **multi-line block** in an
existing file, with **idempotence guaranteed through automatic markers**. It is
the module that fills the gap between `lineinfile:` (1 line) and `template:`
(whole file).

On the next run, Ansible looks for the markers (`# BEGIN ...` and `# END ...`),
**replaces everything between the two** with the new block, and regenerates the
markers. Consequence: **idempotence guaranteed**, never any duplication.

Typical use cases: adding **3-10 hardening lines** to a system file, dropping a
**block of aliases** in `/etc/profile.d/`, managing a **custom section** in a
file you do not fully control.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Insert** an idempotent multi-line block with automatic markers.
2. **Customize** the marker (format, content) to manage **several blocks**.
3. **Position** the block with `insertafter:` / `insertbefore:`.
4. **Adapt** the marker format to the file type (`#`, `--`, `<!-- -->`).
5. **Choose** between `lineinfile:`, `blockinfile:`, and `template:` depending on the size of the content.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/profile.d/aliases-rhce.sh /etc/ssh/sshd_config.d/99-ansible.conf"
```

## 📚 Exercise 1 — Simple block with the default marker

Create `lab.yml`:

```yaml
---
- name: Demo blockinfile par defaut
  hosts: db1.lab
  become: true
  tasks:
    - name: Bloc d aliases shell
      ansible.builtin.blockinfile:
        path: /etc/profile.d/aliases-rhce.sh
        create: true
        mode: "0644"
        block: |
          alias ll='ls -lah'
          alias gs='git status'
          alias ports='ss -tulpn'
```

**Run**:

```bash
ansible-playbook labs/modules-fichiers/blockinfile/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /etc/profile.d/aliases-rhce.sh'
```

🔍 **Observation**: the file contains:

```text
# BEGIN ANSIBLE MANAGED BLOCK
alias ll='ls -lah'
alias gs='git status'
alias ports='ss -tulpn'
# END ANSIBLE MANAGED BLOCK
```

**Re-run**: `changed=0` (idempotence via marker).

**Modify the `block:`** (add `alias rm='rm -i'`) then re-run: `changed=1`,
the block is **updated between the markers**, not duplicated.

## 📚 Exercise 2 — Custom marker (several blocks in one file)

```yaml
- name: Bloc 1 - Durcissement sshd
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config.d/99-ansible.conf
    create: true
    mode: "0600"
    block: |
      PermitRootLogin no
      PasswordAuthentication no
    marker: "# {mark} HARDENING ANSIBLE"

- name: Bloc 2 - Logging custom
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config.d/99-ansible.conf
    block: |
      LogLevel VERBOSE
      SyslogFacility AUTH
    marker: "# {mark} LOGGING ANSIBLE"
```

🔍 **Observation**: the file contains **2 distinct blocks**, each with its own
markers:

```text
# BEGIN HARDENING ANSIBLE
PermitRootLogin no
PasswordAuthentication no
# END HARDENING ANSIBLE
# BEGIN LOGGING ANSIBLE
LogLevel VERBOSE
SyslogFacility AUTH
# END LOGGING ANSIBLE
```

**Without a custom marker**, the 2 tasks would have used the same default marker
(`# {mark} ANSIBLE MANAGED BLOCK`) → the 2nd task would have **overwritten** the
1st. With custom markers, clean **coexistence**.

**`{mark}`** is replaced by `BEGIN` or `END`. Convention: a unique name per block.

## 📚 Exercise 3 — `insertafter:` / `insertbefore:`

```yaml
- name: Inserer un bloc apres une ligne specifique
  ansible.builtin.blockinfile:
    path: /etc/myapp.conf
    create: true
    mode: "0644"
    block: |
      log_level = INFO
      log_path = /var/log/myapp/
    insertafter: '^\[server\]'
    marker: "# {mark} LOGGING"
```

🔍 **Observation**: if the file contains `[server]`, the block is inserted
**just after** that line. Otherwise, the block is inserted at `EOF` (default).

**`insertbefore:`** does the opposite: handy to add a block before an existing
section (e.g. before `[End]`).

**Pitfall**: if the regex matches **several lines**, it is the **last** one that
wins (for `insertafter:`) or the **first** (for `insertbefore:`).

## 📚 Exercise 4 — Removing a block (`state: absent`)

```yaml
- name: Retirer le bloc HARDENING
  ansible.builtin.blockinfile:
    path: /etc/ssh/sshd_config.d/99-ansible.conf
    marker: "# {mark} HARDENING ANSIBLE"
    state: absent
```

🔍 **Observation**: Ansible looks for the `BEGIN HARDENING ANSIBLE` and
`END HARDENING ANSIBLE` markers and **removes everything between the two**
(markers included). The rest of the file is intact.

**Important**: removal requires **the exact marker** used at creation. If you
change the `marker:` between creation and removal, the block becomes
**orphaned** (Ansible no longer finds it).

## 📚 Exercise 5 — Adapt the marker to the file format

For files where **`#` is not a comment**, adapt the marker:

```yaml
# YAML (# est commentaire, OK par defaut)
- ansible.builtin.blockinfile:
    path: /etc/myapp.yml
    block: |
      key1: value1
      key2: value2
    marker: "# {mark} ANSIBLE"

# XML (commentaire = <!-- ... -->)
- ansible.builtin.blockinfile:
    path: /etc/myapp.xml
    block: |
      <option>value1</option>
      <option>value2</option>
    marker: "<!-- {mark} ANSIBLE -->"

# SQL (commentaire = -- ...)
- ansible.builtin.blockinfile:
    path: /etc/myapp.sql
    block: |
      CREATE TABLE foo (...);
      INSERT INTO foo ...;
    marker: "-- {mark} ANSIBLE"

# Python (commentaire = #, OK par defaut)
- ansible.builtin.blockinfile:
    path: /opt/myapp/config.py
    block: |
      DEBUG = True
      LOG_LEVEL = "INFO"
    marker: "# {mark} ANSIBLE"
```

🔍 **Observation**: adapting the marker to the format **prevents the file from
becoming syntactically broken**. A `# BEGIN ANSIBLE` in an XML file would make
the XML invalid.

## 📚 Exercise 6 — The pitfall: 2 `blockinfile:` tasks without a custom marker

```yaml
- name: Bloc 1 (sans marker custom)
  ansible.builtin.blockinfile:
    path: /tmp/lab-blockinfile-piege.txt
    create: true
    block: |
      ligne 1A
      ligne 1B

- name: Bloc 2 (sans marker custom non plus !)
  ansible.builtin.blockinfile:
    path: /tmp/lab-blockinfile-piege.txt
    block: |
      ligne 2A
      ligne 2B
```

**Run and inspect**:

```bash
ansible-playbook labs/modules-fichiers/blockinfile/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /tmp/lab-blockinfile-piege.txt'
```

🔍 **Observation**: the file contains only **block 2** (`ligne 2A`, `ligne 2B`).
The **block 1 was overwritten** because both tasks use the **same default
marker** (`# BEGIN ANSIBLE MANAGED BLOCK`).

**Always** set a **unique marker** per block in the same file.

## 📚 Exercise 7 — Comparison `lineinfile:` vs `blockinfile:` vs `template:`

| Case | Recommended module | Why |
|---|---|---|
| 1 line (`PermitRootLogin no`) | `lineinfile:` | Simple, regex |
| 3-10 related lines (block of options) | `blockinfile:` | Markers, idempotence |
| Whole owned file | `template:` | Interpolation, validate |
| Several separate blocks in a file | `blockinfile:` × N (custom marker) | Coexistence |
| File you do not own (system) | `blockinfile:` | Modifies without rewriting everything |

## 🔍 Observations to note

- **Markers** = `# BEGIN ANSIBLE MANAGED BLOCK` / `# END ...` by default.
- **`{mark}` in `marker:`** is replaced by `BEGIN` or `END`.
- **Unique marker per block** if several blocks in one file.
- **`create: true`** creates the file if it does not exist.
- **`state: absent`** removes everything between the markers.
- **Adapt the marker format** to the file type (`#`, `--`, `<!-- -->`).
- **Always `mode: "0644"`** quoted.

## 🤔 Reflection questions

1. You manage a `/etc/sysctl.conf` file shared between several Ansible roles.
   How do you **avoid conflicts** between the blocks managed by each role?

2. What is the difference between `blockinfile:` (with markers) and `template:`
   from a **traceability** standpoint (who modified what)?

3. You want to add a block **before** an existing line in a file. Why can
   `insertbefore:` be a problem if the regex matches **several** lines?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`marker_begin:`** / **`marker_end:`**: override the end of the marker
  (instead of the `{mark}` template). For cases where you want truly custom
  markers.
- **`prepend_newline:`** / **`append_newline:`**: add a line break before or
  after the inserted block (useful for readability).
- **`drop-in config` pattern**: prefer **a dedicated file** in
  `/etc/<service>.conf.d/99-ansible.conf` managed by `template:` or `copy:`
  rather than a `blockinfile:` in the global file. More modular.
- **Lab 30 (lineinfile vs template)**: full comparison of the 3 approaches.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-fichiers/blockinfile/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-fichiers/blockinfile/challenge/solution.yml

# Production profile (the strictest, target RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/blockinfile/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a pre-commit
> hook to block any commit that would introduce anti-patterns.
