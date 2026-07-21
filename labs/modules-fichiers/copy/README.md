# Lab 31 — `copy:` module (transfer and inline content)

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

🔗 [**Ansible copy module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-copy/)

`ansible.builtin.copy:` is the **transfer** module par excellence. It pushes a
file from the **control node** to the **managed node**, or writes **inline
content** via `content:`. The key difference with `template:`: `copy:` transfers
**as-is**, no Jinja2 interpolation.

Critical options for production: **`mode:`**, **`owner:`**, **`group:`**,
**`backup: true`**, **`validate:`**, and the pitfall of `content:` not
terminated by `\n`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Distinguish** `src:` (local file) and `content:` (inline): when to use which.
2. **Master** the `mode`, `owner`, `group`, `backup`, `force`, `validate` options.
3. **Identify** the pitfall of `content:` without a trailing `\n`.
4. **Avoid** the YAML pitfall of an unquoted `mode:`.
5. **Choose** between `copy:` and `template:` depending on whether the file needs interpolation.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
mkdir -p labs/modules-fichiers/copy/files
ansible web1.lab -b -m shell -a "rm -f /etc/issue.net.* /tmp/lab-copy-*.txt /etc/motd-rhce*"
```

## 📚 Exercise 1 — Transferring a local file (`src:`)

Create `files/banner.txt`:

```text
=====================================
   Acces autorise uniquement
   Toute connexion est tracee
=====================================
```

Create `lab.yml`:

```yaml
---
- name: Demo copy src
  hosts: web1.lab
  become: true
  tasks:
    - name: Deployer le banner SSH
      ansible.builtin.copy:
        src: files/banner.txt
        dest: /etc/ssh/banner-rhce
        owner: root
        group: root
        mode: "0644"
        backup: true
```

**Run**:

```bash
ansible-playbook labs/modules-fichiers/copy/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'sudo cat /etc/ssh/banner-rhce && ls -la /etc/ssh/banner-rhce*'
```

🔍 **Observation**:

- First run: `changed=1`, file created.
- Second run: `changed=0` (idempotent, identical SHA1 checksum).
- **If you modify `files/banner.txt`** and re-run: `changed=1`, and a file
  `banner-rhce.<timestamp>~` appears (backup).

## 📚 Exercise 2 — Inline content (`content:`)

```yaml
- name: Marquer le serveur via content inline
  ansible.builtin.copy:
    content: "Serveur RHCE — provisionne le {{ ansible_date_time.iso8601 }}\n"
    dest: /etc/motd-rhce
    owner: root
    group: root
    mode: "0644"
```

🔍 **Observation**:

- No need to create a source file: `content:` injects the string directly.
- The **trailing `\n`** is crucial: without it, `cat /etc/motd-rhce` glues the
  output to the next prompt.
- On every run, `ansible_date_time.iso8601` changes → task **always `changed`**
  (loss of idempotence). To be avoided unless explicitly intended.

## 📚 Exercise 3 — The missing `\n` pitfall

```yaml
- name: Mauvais (pas de \n final)
  ansible.builtin.copy:
    content: "ligne sans newline"
    dest: /tmp/lab-copy-no-newline.txt

- name: Bon (avec \n)
  ansible.builtin.copy:
    content: "ligne avec newline\n"
    dest: /tmp/lab-copy-with-newline.txt
```

**Run and inspect**:

```bash
ansible-playbook labs/modules-fichiers/copy/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'cat -A /tmp/lab-copy-no-newline.txt'
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'cat -A /tmp/lab-copy-with-newline.txt'
```

🔍 **Observation**:

- Without `\n`: `cat -A` shows `ligne sans newline` (no trailing `$`). The shell
  will display `ligne sans newlineansible@web1$` (glued to the prompt).
- With `\n`: `cat -A` shows `ligne avec newline$`, properly terminated.

**Some parsers** (cron, systemd, openrc) **reject** files without a trailing
`\n`. Always terminate `content:` with `\n`.

## 📚 Exercise 4 — `validate:` (reject an invalid config)

Critical pattern for `sshd_config`, `nginx.conf`, `sudoers`.

```yaml
- name: Deployer sshd_config (avec validation)
  ansible.builtin.copy:
    src: files/sshd_config
    dest: /etc/ssh/sshd_config
    mode: "0600"
    backup: true
    validate: 'sshd -t -f %s'
  notify: Reload sshd

handlers:
  - name: Reload sshd
    ansible.builtin.systemd_service:
      name: sshd
      state: reloaded
```

🔍 **Observation**:

- `%s` is replaced by the **path of the temporary file**.
- If `sshd -t` returns `0` → `/etc/ssh/sshd_config` is overwritten, handler notified.
- If `sshd -t` returns `!= 0` → file intact, task **failed**.

**Without `validate:`** a broken sshd_config could **block SSH** on the next
restart: you lose access.

## 📚 Exercise 5 — The YAML pitfall on `mode:`

```yaml
- name: Piege mode non quote
  ansible.builtin.copy:
    content: "test\n"
    dest: /tmp/lab-mode-piege.txt
    mode: 0644          # ❌ YAML interprete comme decimal 644 → 0o1204

- name: Bon mode quote
  ansible.builtin.copy:
    content: "test\n"
    dest: /tmp/lab-mode-ok.txt
    mode: "0644"        # ✅ String, parse en octal correctement
```

🔍 **Observation**: without quotes, YAML parses `0644` as **decimal 644**
(nothing to do with octal). Ansible tries to apply it as a mode → **aberrant**
permissions.

**Rule**: **always** `mode: "0644"` (quoted) or `mode: "u=rw,g=r,o=r"`
(symbolic).

## 📚 Exercise 6 — `force: false` (do not overwrite)

```yaml
- name: Deployer config initiale (sans ecraser)
  ansible.builtin.copy:
    src: files/myapp.conf
    dest: /etc/myapp.conf
    force: false
    mode: "0644"
```

🔍 **Observation**:

- If `/etc/myapp.conf` does not exist → file created (`changed`).
- If it exists → task **`ok`** (no modification, even if the local content differs).

**Use case**: deploying an initial config that you **let the user modify**.
Handy for `motd` files or example config templates.

## 📚 Exercise 7 — `remote_src: true` (copy from the managed node)

`copy: remote_src: true` does **not** transfer from the control node: it copies
**inside the managed node**.

```yaml
- name: Sauvegarder /etc/hosts en /tmp avant modification
  ansible.builtin.copy:
    src: /etc/hosts
    dest: /tmp/hosts.backup
    remote_src: true
    mode: "0644"
```

🔍 **Observation**: `src:` is resolved **on the managed node side**, not the
control node side. Handy for local backups before modification.

## 🔍 Observations to note

- **`src:`** = local file (control node), **`content:`** = inline.
- **Always `\n`** at the end of `content:`, a classic pitfall of strict parsers.
- **Always `mode: "0644"`** quoted, otherwise YAML decimal vs octal.
- **`backup: true`** = free safety net, to enable on critical configs.
- **`validate:`** is mandatory for `sshd_config`, `nginx.conf`, `sudoers`.
- **`remote_src: true`** = copy **inside** the managed node.
- **`force: false`** = leave the existing file intact (for initial configs).

## 🤔 Reflection questions

1. You want to deploy a config file that **includes the server hostname**.
   Should you use `copy: content:` with `{{ ansible_hostname }}` or switch to
   `template:`? Why?

2. With `backup: true`, where are the backups created and how do you clean them
   automatically after N days?

3. Why is `validate: 'sshd -t -f %s'` **safer** than `validate: 'sshd -t'`
   (without `%s`)? What happens without `%s`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`directory_mode:`**: mode of the **parent directories** created by `copy:`
  when the `dest:` includes a deep path.
- **`unsafe_writes: true`**: allows writing on filesystems that do not support
  atomic `rename` (NFS without locks, some Docker images).
- **`decrypt: true`**: decrypts the source file if encrypted with **Ansible
  Vault**, to push encrypted secrets in cleartext onto the managed node.
- **Multi-file pattern**: `copy: src:` accepts a directory, Ansible
  **synchronizes** recursively (prefix `src: files/`, trailing slash = content,
  no slash = directory).
- **Lab 32 (file)**: to manage **only** the metadata (mode, owner, state)
  without transferring any content.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-fichiers/copy/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-fichiers/copy/challenge/solution.yml

# Production profile (the strictest, target RHCE 2026)
ansible-lint --profile production labs/modules-fichiers/copy/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a pre-commit
> hook to block any commit that would introduce anti-patterns.
