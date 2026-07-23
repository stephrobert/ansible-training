# Lab 24 — `failed_when:` and `changed_when:` (redefine success and change)

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

🔗 [**failed_when and changed_when in Ansible: redefine success and change**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/failed-when-changed-when/)

By default, Ansible considers a `command:` or `shell:` task **`failed`**
if the return code (`rc`) is different from 0, and **`changed`** in every case.
Both behaviors can be **redefined**:

- **`failed_when:`** = an expression that, if true, marks the task as `failed`.
- **`changed_when:`** = an expression that, if true, marks the task as `changed`.

These two directives are **essential for making `command:`/`shell:` idempotent**:
without them, a shell command is **always `changed`**, which pollutes the logs
and triggers handlers wrongly.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Disable** the default `changed` on read-only commands (`changed_when: false`).
2. **Define** a `changed_when:` based on the output (string match, regex).
3. **Redefine** the `failed_when:` to accept certain return codes as success.
4. **Combine** `failed_when: + changed_when:` for an idempotent module.
5. **Diagnose** a module that reports `changed` wrongly.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
```

## 📚 Exercise 1 — The problem: `command:` always `changed`

Create `lab.yml`:

```yaml
---
- name: Demo command toujours changed
  hosts: db1.lab
  become: true
  tasks:
    - name: Lire la version d openssl
      ansible.builtin.command: openssl version
      register: ssl_version
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml
```

🔍 **Observation**: `PLAY RECAP` shows `changed=1`. Yet **reading** a version
**changes nothing**: the task **should be `ok=1, changed=0`**. This is a classic
log pollution.

**Worse**: if this task `notify:` a handler, the handler would run on every run
**wrongly** (a useless service reload).

## 📚 Exercise 2 — `changed_when: false` on reads

Modify the task:

```yaml
- name: Lire la version d openssl (lecture seule)
  ansible.builtin.command: openssl version
  register: ssl_version
  changed_when: false
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml
```

🔍 **Observation**: `PLAY RECAP` now shows `ok=1, changed=0`. The task is
explicitly marked as **read-only**.

**Rule**: `changed_when: false` on **any** command that only reads
(`cat`, `grep`, `openssl version`, `which`, `stat`, etc.).

## 📚 Exercise 3 — `changed_when:` with an expression on the output

For commands that may or may not **modify** something, use an expression on
the output to detect the change.

Real case: `git pull` changes something **only** if there are new commits.
You can detect it via the output that contains "Already up to date" or not.

```yaml
- name: Simulation git pull (changed seulement si nouveau)
  ansible.builtin.command: |
    echo "{{ 'Already up to date.' if simulate_no_change | default(true) | bool else 'Updating abc..def' }}"
  register: pull_result
  changed_when: "'Already up to date' not in pull_result.stdout"
```

**Run**:

```bash
# 1st run: simulate_no_change=true (default) → ok=1
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml

# 2nd run: simulate_no_change=false → changed=1
ansible-playbook labs/ecrire-code/failed-when-changed-when/lab.yml \
  --extra-vars "simulate_no_change=false"
```

🔍 **Observation**: the same shell command reports `ok=1` or `changed=1`
depending on its output. This is **idempotence done by hand** on a `command:`.

## 📚 Exercise 4 — `failed_when:` to accept specific return codes

Classic case: `grep` returns **`rc=1` when it does not find** the string, and
Ansible treats that as a failure. But for an audit, it is often **a success**.

```yaml
- name: Verifier si root login est desactive (rc 1 = absent = OK)
  ansible.builtin.command: grep -E "^PermitRootLogin no" /etc/ssh/sshd_config
  register: grep_result
  failed_when: grep_result.rc not in [0, 1]
  changed_when: false
```

🔍 **Observation**:

- **rc=0**: found → task `ok`.
- **rc=1**: not found → task `ok` too (because `1 in [0, 1]` is true, so `failed_when` is false).
- **rc=2+**: another error (missing file, etc.) → task **failed**.

**Without `failed_when:`**, the `rc=1` would have failed the task, and you would
need a heavy `block/rescue` or a dangerous `ignore_errors: true`.

## 📚 Exercise 5 — Combining `failed_when: + changed_when:` (full idempotence)

Full pattern to make a shell command **idempotent** (equivalent to a native
module):

```yaml
- name: Activer SELinux en enforcing (idempotent)
  ansible.builtin.shell: |
    current=$(getenforce)
    if [ "$current" != "Enforcing" ]; then
      setenforce 1
      echo "CHANGED"
    else
      echo "OK"
    fi
  register: selinux_result
  changed_when: "'CHANGED' in selinux_result.stdout"
  failed_when: false  # The shell handles the cases itself
```

🔍 **Observation**:

- 1st run: SELinux not enforcing → output `CHANGED` → task `changed`.
- 2nd run: already enforcing → output `OK` → task `ok`.

This is exactly like the idempotence of **builtin modules**, but coded by hand
because `setenforce` has no native module.

**Better**: use **`ansible.posix.selinux`** (dedicated module). Always prefer a
native module when one exists.

## 📚 Exercise 6 — The pitfall: a badly written `failed_when:`

```yaml
# ❌ Wrong: Jinja2 interpretation
- name: Mauvaise expression
  ansible.builtin.command: echo hello
  register: r
  failed_when: "{{ r.rc != 0 }}"  # ❌ No need for {{ }}

# ✅ Good
- name: Bonne expression
  ansible.builtin.command: echo hello
  register: r
  failed_when: r.rc != 0
```

🔍 **Observation**: `failed_when:` and `changed_when:` are **already Jinja2
expressions**, so do **not** add `{{ }}` (Ansible warning since 2.16).

**Another pitfall**: confusing `or` / `and`. `failed_when: r.rc != 0 or 'Error' in r.stdout`
is more restrictive than `r.rc != 0` alone. Think carefully about the semantics.

## 🔍 Observations to note

- **`changed_when: false`** on **any** read-only command (audit, query).
- **`changed_when:` with an expression** makes `command:` / `shell:` idempotent.
- **`failed_when:` with a list of codes** = accept certain rc as success.
- **`failed_when:` + `changed_when:`** combined let you write a "module by hand".
- **No `{{ }}` in `when:`, `failed_when:`, `changed_when:`**: they are already expressions.
- **Prefer a native module** when one exists (selinux, sysctl, lineinfile) rather
  than `shell:` + `failed_when` / `changed_when`.

## 🤔 Reflection questions

1. You run `dnf check-update`, which returns **`rc=100` when updates are
   available**. How do you write the `failed_when:` so that `rc=0` (up to date) and
   `rc=100` (updates available) are both **successes**, but other codes fail?

2. Why is a `changed_when: false` on a `command:` task in a **rolling update**
   play **important**? (hint: think about handlers).

3. What is the difference between `failed_when: false` (forces `failed=False`)
   and `ignore_errors: true` (lab 24)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`failed_when:` with a list**: `failed_when: ['fatal' in r.stderr, r.rc not in [0,1]]`
  is an **implicit OR** between the list conditions (like `when:`).
- **`unreachable_when:` does not exist**: to handle an unreachable host, use
  `block/rescue` at the play level or `serial: + max_fail_percentage:`.
- **`check_mode:` + `changed_when:`**: a `command:` in `--check` does not run by
  default. Force it with `check_mode: false` + `changed_when: false` for an audit
  during check mode (lab 08).
- **`dry-run` + `apply` pattern**: a single shell task that takes `--dry-run`
  depending on a variable and uses `changed_when:` on the output. It gives a single
  test/apply mode.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/failed-when-changed-when/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/failed-when-changed-when/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/failed-when-changed-when/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
