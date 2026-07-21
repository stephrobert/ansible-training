# Lab 30 — `lineinfile:` vs `template:` (when to use which)

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

🔗 [**lineinfile vs template in Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/lineinfile-vs-template/)

Two modules to **modify config files**, two opposite philosophies:

- **`lineinfile:`** = line-by-line surgery. You do **not own** the whole file:
  you add/modify **1 or 2 lines** targeted by regex. Keeps the rest intact.
- **`template:`** = full rewrite. You **own** the file: you regenerate everything
  from a Jinja2 template.

Choosing the wrong module leads to **two different problems**:

- `lineinfile:` on 20 lines → 20 tasks, fragile regexes, unreadable.
- `template:` on a file you do not own → you overwrite the modifications of the
  user or of other tools.

This lab demonstrates the **two modules** side by side on concrete cases.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Choose** between `lineinfile:` and `template:` depending on the scenario.
2. **Use** `lineinfile:` with `regexp:`, `line:`, `state:`, `backup:`.
3. **Combine** the two modules: `template:` for the base, `lineinfile:` for overrides.
4. **Identify** the threshold where `lineinfile:` becomes `blockinfile:` or `template:`.
5. **Diagnose** a `lineinfile:` that stacks up instead of replacing (missing regex).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/myapp.conf*; rm -f /etc/hosts.bak"
```

## 📚 Exercise 1 — Simple `lineinfile:` (1 line)

```yaml
---
- name: Demo lineinfile - 1 ligne
  hosts: db1.lab
  become: true
  tasks:
    - name: Ajouter une entree DNS dans /etc/hosts
      ansible.builtin.lineinfile:
        path: /etc/hosts
        regexp: '^192\.168\.99\.99\s'
        line: '192.168.99.99 mon-host.lab'
        state: present
        backup: true
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/lineinfile-vs-template/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /etc/hosts'
```

🔍 **Observation**: the line `192.168.99.99 mon-host.lab` is added to
`/etc/hosts`. **The rest of the file is intact**: Ansible rewrote nothing.

**Re-run the playbook**: no modification (idempotent thanks to the `regexp:`).

## 📚 Exercise 2 — `lineinfile:` with `regexp:` (modify an existing line)

```yaml
- name: Modifier la valeur de PermitRootLogin
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'
    state: present
    backup: true
    validate: 'sshd -t -f %s'
```

🔍 **Observation**:

- **`regexp:`** matches the **existing** line (commented or uncommented).
- **`line:`** **replaces** it with the new value.
- **Without `regexp:`**, Ansible **adds** a new line (and stacks up on every run).

**Always** set `regexp:` when you modify an existing option. Without regexp,
on the 2nd run you have **2 lines `PermitRootLogin no`**.

## 📚 Exercise 3 — `template:` for a complete file

For an **application** config file (myapp.conf), `template:` is cleaner.

Create `templates/myapp.conf.j2`:

```jinja
[server]
host = {{ server.host }}
port = {{ server.port }}
workers = {{ server.workers }}

[database]
url = {{ database.url }}
pool_size = {{ database.pool_size }}
```

```yaml
- name: Generer myapp.conf depuis template
  ansible.builtin.template:
    src: templates/myapp.conf.j2
    dest: /etc/myapp.conf
    owner: root
    group: root
    mode: "0644"
    backup: true
```

🔍 **Observation**: the file is **generated completely** from the template. No
need for 5 separate `lineinfile:` for 5 sections. Simpler maintenance.

## 📚 Exercise 4 — Demonstrate the difference on the same file

Suppose we want to manage `/etc/myapp.conf`, which has 6 lines:

**`lineinfile:` approach (wrong choice here)**:

```yaml
- ansible.builtin.lineinfile:
    path: /etc/myapp.conf
    regexp: '^host'
    line: 'host = 0.0.0.0'

- ansible.builtin.lineinfile:
    path: /etc/myapp.conf
    regexp: '^port'
    line: 'port = 8080'

- ansible.builtin.lineinfile:
    path: /etc/myapp.conf
    regexp: '^workers'
    line: 'workers = 4'

# ... 3 other lineinfile for [database]
```

🔍 **Problems**:

- **6 tasks** instead of 1.
- The **`[server]`** and `[database]` sections are not managed (Ansible does not
  understand the INI structure).
- If an expected line is **missing** at first, `lineinfile:` **adds it at the end
  of the file**, not in the right section!

**`template:` approach (good choice)**:

```yaml
- ansible.builtin.template:
    src: templates/myapp.conf.j2
    dest: /etc/myapp.conf
```

→ **A single task**, structure preserved, idempotent code.

## 📚 Exercise 5 — Combine the two: `template:` + `lineinfile:`

Real pattern: you generate `nginx.conf` via `template:`, but you want to **add
a line** in `/etc/sysctl.conf` (a file you do not own, managed by several tools).

```yaml
- name: Generer nginx.conf depuis template (controle complet)
  ansible.builtin.template:
    src: templates/nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    validate: 'nginx -t -c %s'
  notify: Reload nginx

- name: Ajouter une ligne dans sysctl.conf (cohabitation avec d autres outils)
  ansible.builtin.lineinfile:
    path: /etc/sysctl.conf
    regexp: '^net.core.somaxconn'
    line: 'net.core.somaxconn = 4096'
  notify: Apply sysctl

handlers:
  - name: Reload nginx
    ansible.builtin.systemd_service:
      name: nginx
      state: reloaded

  - name: Apply sysctl
    ansible.builtin.command: sysctl -p
```

🔍 **Observation**: `template:` for the **app-specific** files you control;
`lineinfile:` for the **shared** files (`/etc/hosts`,
`/etc/sysctl.conf`, `/etc/security/limits.conf`).

## 📚 Exercise 6 — The pitfall: `lineinfile:` without `regexp:` stacks up

```yaml
# ❌ Wrong: no regexp
- ansible.builtin.lineinfile:
    path: /tmp/lab-piege.txt
    line: 'option = valeur'
    create: true
```

**Run 3 times**:

```bash
for i in 1 2 3; do
  ansible-playbook labs/ecrire-code/lineinfile-vs-template/lab.yml
done
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /tmp/lab-piege.txt'
```

🔍 **Observation**: without `regexp:`, Ansible **checks whether the line already
exists exactly**. If you change just one character (space, case), it is
added again → **a file that grows**.

**Solution**: **always** set a `regexp:` that matches the **key** (`^option\s*=`),
even if the full `line:` changes.

```yaml
# ✅ Good: regexp on the key
- ansible.builtin.lineinfile:
    path: /tmp/lab-piege.txt
    regexp: '^option\s*='
    line: 'option = valeur'
```

## 📚 Exercise 7 — When to move from `lineinfile:` to `blockinfile:`?

`blockinfile:` (lab 33 later) manages **a block of several lines** with
automatic markers. When to prefer it?

| Case | Module |
|---|---|
| 1 line (`option = valeur`) | `lineinfile:` |
| 2-3 related lines (block of options) | `blockinfile:` |
| Full owned file | `template:` |

**Rule**: if you have **3+ consecutive `lineinfile:`** on the same file,
move to **`blockinfile:`** (1 task, markers, idempotent).

## 🔍 Observations to note

- **`lineinfile:`** = 1 line, **`template:`** = full file.
- **`regexp:`** = mandatory to modify an existing line (otherwise it stacks up).
- **`backup: true`** + **`validate:`** = safety combo on critical configs.
- **`template:`** on an **owned** file; **`lineinfile:`** on a **shared** file.
- **3+ consecutive `lineinfile:`** = move to `blockinfile:` (lab 33).
- **`lineinfile:` without `regexp:`** = classic pitfall (stacks up on every change of the line).

## 🤔 Reflection questions

1. You want to modify `/etc/sudoers` to add a rule. `lineinfile:` or
   `template:`? Why is `validate: 'visudo -cf %s'` **critical**?

2. You generate `/etc/hosts` via `template:` from a loop over `groups['all']`.
   What is the **risk** compared to a `lineinfile:` that would just add a line?

3. You have 5 lines to add in `/etc/sysctl.conf`. Compare the approaches:
   5 `lineinfile:`, 1 `blockinfile:`, or 1 full `template:` for `/etc/sysctl.d/99-myapp.conf`.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`lineinfile: insertafter:`** / **`insertbefore:`**: position the line
  added after/before a marker. Ex: add after `^# Custom rules` in sudoers.
- **`replace:`** module: **multi-occurrence** substitution by regex. Different
  from `lineinfile:`, which handles only a single line.
- **`drop-in config` pattern**: avoid modifying `/etc/<service>.conf` (global
  file); drop a custom file into `/etc/<service>.conf.d/99-myapp.conf`
  via `template:`. Cleaner, more modular.
- **`lineinfile: state: absent`** + `regexp:`: **remove** a line matching
  the regexp. Handy for **hardening** (removing dangerous options).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/lineinfile-vs-template/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
