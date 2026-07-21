# Lab 53 — `assert:` and `fail:` modules (defensive validation)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.

## 🧠 Recap

🔗 [**Ansible assert and fail modules**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-assert-fail/)

Two complementary modules for **defensive programming**:

- **`ansible.builtin.assert:`** validates a **condition**; if it is false, the
  play fails with a clear message. **Precondition** pattern at the start of a play.
- **`ansible.builtin.fail:`** fails **explicitly** with a custom message.
  **Error branch** pattern inside conditional logic.

Semantic difference: `assert:` expresses "this **must** be true"; `fail:`
expresses "I stop **now** because such a condition is met".

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Validate** **prerequisites** at the start of a play with `assert:`.
2. **Customize** messages with `fail_msg:` / `success_msg:`.
3. **Fail explicitly** with `fail:` + `when:` (error branch).
4. **Combine** `assert:` with **Jinja2 tests** (`is defined`, `is integer`).
5. **Choose** between `assert:`, `fail:`, and `failed_when:` depending on context.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
```

## 📚 Exercise 1 — Simple `assert:`

Create `lab.yml`:

```yaml
---
- name: Demo assert
  hosts: db1.lab
  vars:
    app_port: 8080
  tasks:
    - name: Valider que app_port est dans la plage non-privilegiee
      ansible.builtin.assert:
        that:
          - app_port is defined
          - app_port is integer
          - app_port > 1024
          - app_port < 65535
        fail_msg: "app_port doit etre un entier entre 1024 et 65535 (recu : {{ app_port | default('absent') }})"
        success_msg: "Validation OK : app_port = {{ app_port }}"
```

**Run**:

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/lab.yml
```

🔍 **Observation**:

- If **all conditions** are true → `success_msg` is displayed, the play continues.
- If **one condition fails** → `fail_msg` is displayed, the play is **failed**.

**Test the failure**:

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/lab.yml \
  --extra-vars "app_port=42"
# → fail_msg : app_port doit etre un entier entre 1024 et 65535 (recu : 42)
```

## 📚 Exercise 2 — Magic variables in `that:`

```yaml
- name: Valider plusieurs aspects de l environnement
  ansible.builtin.assert:
    that:
      - ansible_distribution in ['AlmaLinux', 'RedHat', 'Rocky']
      - ansible_distribution_major_version | int >= 9
      - ansible_memtotal_mb >= 1024
      - 'wheel' in (ansible_local | default({}) | dict2items | map(attribute='value') | list | flatten | default([]))
    fail_msg: |
      Pre-requis non remplis :
      - OS attendu : RHEL/AlmaLinux/Rocky 9+ (vu : {{ ansible_distribution }} {{ ansible_distribution_major_version }})
      - Memoire min : 1Go (vu : {{ ansible_memtotal_mb }} Mo)
```

🔍 **Observation**: `that:` accepts a **list** of conditions = implicit AND.
**`fail_msg:`** can be multi-line for a complete diagnostic.

## 📚 Exercise 3 — `fail:` (explicit failure with when)

```yaml
- name: Detecter un environnement non supporte
  ansible.builtin.fail:
    msg: |
      Environnement non supporte :
      - OS : {{ ansible_distribution }}
      - Version : {{ ansible_distribution_version }}
      Ce playbook necessite RHEL/AlmaLinux 9+.
  when: ansible_distribution not in ['AlmaLinux', 'RedHat', 'Rocky']
        or ansible_distribution_major_version | int < 9
```

🔍 **Observation**: **`fail:`** is a task that **always fails** (when it runs).
`when:` conditions it. Explicit **error branch** pattern.

**`assert:` vs `fail:` + `when:`**:

```yaml
# Equivalent fonctionnel
- ansible.builtin.assert:
    that: ansible_distribution_major_version | int >= 9
    fail_msg: "RHEL 9+ requis"

- ansible.builtin.fail:
    msg: "RHEL 9+ requis"
  when: ansible_distribution_major_version | int < 9
```

**Prefer `assert:`** when the **condition is positive** ("this must be true").
**Prefer `fail:`** when the logic is an explicit **error branch** (e.g. "if the
OS is X, we do not support it").

## 📚 Exercise 4 — Play precondition pattern

```yaml
- name: Deploy myapp
  hosts: webservers
  become: true
  pre_tasks:
    - name: Pre-requis - OS
      ansible.builtin.assert:
        that:
          - ansible_distribution in ['AlmaLinux', 'RedHat', 'Rocky']
        fail_msg: "OS non supporte"

    - name: Pre-requis - paquets installes
      ansible.builtin.command: rpm -q chrony firewalld
      register: pkgs_check
      changed_when: false
      failed_when: pkgs_check.rc != 0

    - name: Pre-requis - port libre
      ansible.builtin.wait_for:
        port: 8080
        host: 127.0.0.1
        state: stopped
        timeout: 5

  tasks:
    # ... real deploy tasks
```

🔍 **Observation**: `pre_tasks:` is a section dedicated to **preconditions**.
If an `assert:` fails inside it, the `tasks:` do **not** run. A clean
**fail-fast** pattern.

## 📚 Exercise 5 — Jinja2 tests in `assert:`

```yaml
- name: Valider la structure d une variable complexe
  vars:
    db_config:
      host: db1.lab
      port: 5432
      pool_size: 10
  ansible.builtin.assert:
    that:
      - db_config is defined
      - db_config is mapping              # is a dict
      - db_config.host is defined
      - db_config.host is string
      - db_config.port is defined
      - db_config.port is integer
      - db_config.port > 0
      - db_config.port < 65536
      - db_config.pool_size is integer
      - db_config.pool_size > 0
    fail_msg: "Structure de db_config invalide — voir les conditions ci-dessus"
```

🔍 **Observation**: manual **schema validation** pattern. For complex cases, you
combine **several tests** (`is defined`, `is mapping`, `is integer`). See
[Lab 28 — Jinja2 tests](../../ecrire-code/tests-jinja/) for the full list.

## 📚 Exercise 6 — The trap: `assert:` after `register:`

```yaml
- name: Capturer le rc de openssl
  ansible.builtin.command: openssl version
  register: openssl_check
  changed_when: false
  failed_when: false   # Capture even on failure

- name: Valider que la version est >= 3
  ansible.builtin.assert:
    that:
      - openssl_check.rc == 0
      - openssl_check.stdout is search('OpenSSL 3\\.')
    fail_msg: "OpenSSL 3+ requis (vu : {{ openssl_check.stdout | default('non installe') }})"
```

🔍 **Observation**: the **command + register + assert** pattern is very common to
validate a binary version before use. The `failed_when: false` on the `command:`
lets `assert:` produce the **clear error message** instead of the raw module error.

## 📚 Exercise 7 — `quiet: true` for cascading asserts

With dozens of assertions, the noise in the output is annoying. **`quiet:
true`** displays **only** the `fail_msg:` (not the successes).

```yaml
- name: 50 validations silencieuses
  ansible.builtin.assert:
    that:
      - ansible_memtotal_mb >= 1024
    fail_msg: "Memoire insuffisante"
    success_msg: "Memoire OK"
    quiet: true
```

🔍 **Observation**: with `quiet: true`, the assert only pollutes the logs if it
fails. Cleaner console output on **compliance** playbooks (CIS Benchmark, RGS audit).

## 🔍 Observations to note

- **`assert: that:`** = list of conditions, implicit AND.
- **`fail_msg:`** / **`success_msg:`** to customize the messages.
- **`fail:`** = explicit failure, to be combined with `when:`.
- **Prefer `assert:`** for **preconditions** ("this must be true").
- **Prefer `fail:`** for **error branches** ("if X then abort").
- **`pre_tasks:`** is the idiomatic section for validation `assert:`.
- **`quiet: true`** on assert to avoid pollution on audit playbooks.

## 🤔 Reflection questions

1. You want to **validate 10 conditions** in parallel. Do you prefer a
   `assert: that: [c1, c2, ..., c10]` or 10 separate `assert:`? What is the
   trade-off?

2. Semantic difference between `failed_when: rc != 0` (on a `command:`) and
   `assert: that: rc == 0` (in the next task)?

3. You want to **continue the play** even if the assert fails (to collect all
   the warnings). Which pattern (`ignore_errors:`, `block/rescue`, or custom)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`debug: msg:`** to display without failing (equivalent of Python `print`).
- **`pause: prompt:`** to ask for an **interactive confirmation** before a
  critical operation.
- **`meta: end_play`** to end the play **cleanly** without error when a
  condition is met (different from `fail:` which returns `failed=1`).
- **`assert + when` pattern**: `when: var | bool` on an `assert:` to condition
  it to the runs where it is relevant.
- **Lab 51 (`stat:`) + `assert:`**: powerful combination, check existence +
  validate the attributes.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-diagnostic/assert-fail/lab.yml
ansible-lint labs/modules-diagnostic/assert-fail/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/assert-fail/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
