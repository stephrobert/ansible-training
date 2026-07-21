# Lab 25 — `ignore_errors:` (legitimate use vs anti-pattern)

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

🔗 [**ignore_errors in Ansible: legitimate use vs anti-pattern**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/ignore-errors/)

`ignore_errors: true` lets a task **fail** without **stopping the play**. The
task stays marked `failed`, but Ansible moves to the next one. It is the
**equivalent of Python's `try: ... except: pass`**: handy but often an anti-pattern
because it **hides the real errors**.

In 99% of cases, **`failed_when:`** (lab 24) or **`block/rescue`** (lab 23) are
preferable. `ignore_errors:` remains useful in **3 specific legitimate cases**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Understand** the effect of `ignore_errors: true` on the PLAY RECAP.
2. **Identify** the **3 legitimate cases** where `ignore_errors` is acceptable.
3. **Prefer** `failed_when:` or `block/rescue` in all other cases.
4. **Combine** `ignore_errors:` with `register:` to condition what follows.
5. **Diagnose** a playbook that silently hides errors.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
```

## 📚 Exercise 1 — The default behavior (without `ignore_errors:`)

Create `lab.yml`:

```yaml
---
- name: Demo sans ignore_errors
  hosts: db1.lab
  become: true
  tasks:
    - name: Tache 1 - OK
      ansible.builtin.debug:
        msg: "tache 1"

    - name: Tache 2 - echec garanti
      ansible.builtin.command: /bin/false

    - name: Tache 3 - jamais executee
      ansible.builtin.debug:
        msg: "tache 3"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/ignore-errors/lab.yml
```

🔍 **Observation**: **task 2 crashes**, the play **stops**, **task 3 never
runs**. PLAY RECAP: `failed=1`. This is the standard behavior.

## 📚 Exercise 2 — With `ignore_errors: true`

Modify task 2:

```yaml
- name: Tache 2 - echec mais on continue
  ansible.builtin.command: /bin/false
  ignore_errors: true
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/ignore-errors/lab.yml
```

🔍 **Observation**:

- Console output: `TASK [Tache 2 - echec mais on continue] : FAILED!` then
  `...ignoring`.
- **Task 3 runs**.
- PLAY RECAP: **`failed=0` but `ignored=1`**.

This is the **controlled silencing**: the error is logged but does not stop the play.
The PLAY RECAP shows `ignored=1` for visibility.

## 📚 Exercise 3 — Legitimate case #1: opportunistic cleanup

Pattern: delete a file that may or may not exist, without a prior `stat:` condition.

```yaml
- name: Nettoyer un eventuel lock orphelin
  ansible.builtin.file:
    path: /var/run/myapp.lock
    state: absent
  ignore_errors: true
```

🔍 **Observation**: if `/var/run/myapp.lock` exists → deleted. If it does not exist
→ task `ok` (no error). **If the module fails for another reason** (permission,
read-only filesystem), `ignore_errors:` hides that error. **Bad usage**.

**Better**: use `state: absent` directly on the `file:` module (which is
**idempotent** and does not fail on a missing file). **No need for `ignore_errors:`**.

→ This case is in fact **not legitimate** because the module already handles the absence.

## 📚 Exercise 4 — Legitimate case #2: audit / info gathering

Pattern: an **audit** play where you collect info on N hosts and accept that
some are unreachable or have missing facts.

```yaml
- name: Audit des services
  hosts: all
  tasks:
    - name: Tester si nginx est installe
      ansible.builtin.command: rpm -q nginx
      register: nginx_check
      ignore_errors: true
      changed_when: false

    - name: Marquer le statut nginx
      ansible.builtin.debug:
        msg: "nginx sur {{ inventory_hostname }} : {{ 'installe' if nginx_check.rc == 0 else 'absent' }}"
```

🔍 **Observation**: `rpm -q` returns `rc=1` if the package is not installed. With
`ignore_errors: true`, you capture the rc in `register:` and use it later.

**But!** This task would be better written with `failed_when: false` (functionally
equivalent but semantically clearer for an audit):

```yaml
- name: Tester si nginx est installe (audit-style)
  ansible.builtin.command: rpm -q nginx
  register: nginx_check
  failed_when: false
  changed_when: false
```

→ This case is **a case where `failed_when: false` is preferable to `ignore_errors:`**.

## 📚 Exercise 5 — Legitimate case #3: non-critical optional task

Pattern: send a Slack notification at the end of a deploy. If Slack is down, the
deploy is still a success.

```yaml
- name: Notifier Slack (best effort)
  ansible.builtin.uri:
    url: https://hooks.slack.com/services/...
    method: POST
    body: '{"text": "Deploy OK"}'
    body_format: json
  ignore_errors: true
```

🔍 **Observation**: if Slack responds `500` or is unreachable, the play continues.
This is legitimate because the notification is **not critical**.

**Preferable variant**: `block/rescue` that **logs the failure** to a file without
stopping the play.

```yaml
block:
  - name: Notifier Slack
    ansible.builtin.uri: ...
rescue:
  - name: Logger l echec de notification
    ansible.builtin.lineinfile:
      path: /tmp/notification-failures.log
      line: "Slack notification failed at {{ ansible_date_time.iso8601 }}"
      create: true
```

→ This case is **acceptable with `ignore_errors:`** but `block/rescue` is more
visible and lets you trace the failure.

## 📚 Exercise 6 — The danger: `ignore_errors:` hides everything

```yaml
# ❌ VERY dangerous
- name: Configurer la base de donnees
  ansible.builtin.shell: |
    /opt/app/setup-db.sh
  ignore_errors: true
```

🔍 **Observation**: if `setup-db.sh` crashes (invalid SQL, wrong password, full
disk), Ansible **continues** the play as if everything was fine. The rest of the
deployment may **succeed** while the **database is broken**.

This is Ansible's **number one anti-pattern**: `ignore_errors:` on critical operations
**hides** major errors.

**Mitigation**:

- **Prefer `failed_when:`** with a precise expression on what constitutes an acceptable
  failure.
- **Use `block/rescue`** to catch and log.
- **Never `ignore_errors:`** on an operation that modifies data.

## 🔍 Observations to note

- **`ignore_errors: true`** does **not** hide the error: it is in `failed=N` of the
  PLAY RECAP in standard mode, but counted as `ignored=N` with ignore_errors.
- **3 legitimate cases** (all better served by other tools):
  1. Opportunistic cleanup → use the module's `state: absent` (idempotent by default).
  2. Audit / gathering → use `failed_when: false` (clearer semantics).
  3. Non-critical notification → use `block/rescue` to log the failure.
- **Anti-pattern**: `ignore_errors:` on critical operations (DB, deploy, secrets).
- **`register:` + `ignore_errors:`** = classic audit pattern, but replace it with `failed_when:`.

## 🤔 Reflection questions

1. You see `ignore_errors: true` 30 times in a legacy repo. What is your
   **first action**: replace it with what, and in what priority order?

2. Why is `ignored=1` in the PLAY RECAP **more dangerous** than `failed=1`?
   (hint: think of an operator scanning the PLAY RECAP quickly).

3. A colleague says "I use `ignore_errors: true` because it is shorter than
   `failed_when: false`". What are the **3 arguments** to change their mind?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`any_errors_fatal: true`** at the play level (lab 25): the opposite of
  `ignore_errors`, it forces the failure of the whole play from the first error,
  useful for cluster operations that must be atomic.
- **`failed_when: false`** (lab 23): a functional equivalent of `ignore_errors:`
  but more expressive (you **explicitly** state that you do not consider the error
  a failure).
- **`block/rescue`** (lab 23): the **real** alternative to catch and **act**
  on the error (notification, rollback, log).
- **Ansible Lint rule `ignore-errors`**: a rule that flags every `ignore_errors: true`
  as a **warning**. Enable it in CI to force a human review.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/ignore-errors/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/ignore-errors/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/ignore-errors/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
