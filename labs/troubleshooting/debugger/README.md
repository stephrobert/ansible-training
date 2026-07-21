# Lab 90 — Interactive Ansible debugger (`debugger: on_failed`)

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

🔗 [**Interactive Ansible debugger**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/debugger-interactif/)

When a task fails in a long playbook, **rerunning everything from the start** is slow and frustrating. Ansible provides an **interactive debugger** that opens a **REPL** at the moment of failure: you inspect variables, **change arguments on the fly** (`task.args['name'] = 'nginx'`), **replay** the modified task (`redo`), and **continue** the playbook (`continue`).

Enabled at task or play level with `debugger: on_failed`. **Essential** for iterating quickly on a bug without rerunning 100 tasks.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Enable** the debugger via `debugger: on_failed` at play/task level.
2. **Inspect** variables (`p task`, `p task.args`, `p task_vars['x']`, `p result`).
3. **Change** a task's args on the fly (`task.args['name'] = 'nginx'`).
4. **Replay** the modified task (`redo`).
5. **Continue** the playbook (`continue`) or abort (`quit`).
6. Understand **when** the debugger is NOT relevant (CI, automated production).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab90-debug.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Target tree layout

```text
labs/troubleshooting/debugger/
├── README.md                       ← guided tutorial
└── challenge/
    ├── README.md                   ← challenge brief
    └── tests/
        └── test_debugger.py        ← pytest+testinfra tests
```

The learner writes `lab.yml` (over the exercises) and `challenge/solution.yml` themselves.

## 📚 Exercise 1 — Enable `debugger: on_failed`

Create a `lab.yml` that **fails on purpose** (nonexistent package):

```yaml
---
- name: Lab 90 — débogueur interactif
  hosts: db1.lab
  become: true
  gather_facts: false
  debugger: on_failed                # ← enables the REPL on failure
  tasks:
    - name: Installer un paquet inexistant
      ansible.builtin.dnf:
        name: nginx-impossible-2026  # ← does not exist
        state: present
```

Run:

```bash
ansible-playbook labs/troubleshooting/debugger/lab.yml
```

Typical output:

```text
TASK [Installer un paquet inexistant] ***
fatal: [db1.lab]: FAILED! => {"msg": "...nginx-impossible-2026..."}

[db1.lab] TASK: Installer un paquet inexistant (debug)>
```

🔍 **Observation**: the **`(debug)>`** prompt indicates you are in the REPL. The task did not rerun the whole play, it stopped **exactly** at the failure. Type `help` for the command list.

## 📚 Exercise 2 — Inspect variables at runtime

At the `(debug)>` prompt:

```text
(debug)> p task
TASK: Installer un paquet inexistant
(debug)> p task.args
{'name': 'nginx-impossible-2026', 'state': 'present'}
(debug)> p task_vars['inventory_hostname']
'db1.lab'
(debug)> p result._result
{'failed': True, 'msg': '...nginx-impossible-2026...', ...}
```

🔍 **Observation**: `p` (print) accepts any Python expression. `task_vars` contains **all** the resolved variables for the host (group_vars, host_vars, facts, play vars). It answers "what value does the variable have at the moment of failure?".

## 📚 Exercise 3 — Change args on the fly + redo

Still at the `(debug)>` prompt:

```text
(debug)> task.args['name'] = 'nginx'
(debug)> redo
ok: [db1.lab]
[db1.lab] TASK: Tâche suivante (debug)>
```

🔍 **Observation**: you **changed** the task at runtime, **replayed** it, and the task passed. **No need to rerun the playbook** or edit the YAML. For a fleet of 50 hosts where a single task breaks, this is invaluable. **`continue`** moves to the next task, **`quit`** aborts.

## 📚 Exercise 4 — `task_vars` is modifiable

If the error comes from a variable:

```yaml
- ansible.builtin.copy:
    dest: /tmp/lab90-debug.txt
    content: "Hello {{ undef_var }}"
    mode: "0644"
```

At the `(debug)>` prompt:

```text
(debug)> task_vars['undef_var'] = 'world'
(debug)> update_task
(debug)> redo
ok: [db1.lab]
```

🔍 **Observation**: `task_vars['x'] = 'y'` injects the variable, **`update_task`** (shortcut `u`) recreates the task with the new vars, then `redo` replays. A powerful workflow to resolve `undefined variable` errors.

## 📚 Exercise 5 — Strategy `linear` vs `free` in debug

```yaml
- hosts: webservers
  strategy: free       # ← independent tasks per host
  debugger: on_failed
```

🔍 **Crucial observation**: with **`strategy: free`**, while you are at the `(debug)>` prompt on web1.lab, **web2.lab's tasks keep running**. Prefer **`strategy: linear`** (default) in debug: a synchronous pause across all hosts.

## 📚 Exercise 6 — When NOT to use the debugger

The debugger is **interactive**. Do not enable it:

- In **CI/CD**: no stdin, the pipeline freezes indefinitely.
- On **AWX / AAP**: jobs have no user prompt.
- In cron / systemd timer: same.

For these contexts, prefer:

- **`ANSIBLE_KEEP_REMOTE_FILES=1`** + **`ansible-navigator` artifacts** (lab 91 + EE).
- **Detailed logs** with **`-vv` or `-vvv`** (lab 89).
- **Molecule tests** on reproducible scenarios (roles labs 62-65).

## 🔍 Observations to note

- **`debugger: on_failed`** at play or task level, not global.
- **`p`** print, accepts any Python expression.
- **`task.args['x'] = ...`** + **`redo`** changes + replays.
- **`task_vars['x'] = ...`** + **`update_task`** (`u`) + **`redo`** changes a variable.
- **`strategy: linear`** mandatory in debug (otherwise free creates races).
- **No debugger in CI**: interactivity required.

## 🤔 Reflection questions

1. Which other values does `debugger:` take? (Hint: `always`, `never`, `on_failed`, `on_unreachable`, `on_skipped`).
2. How do you enable the debugger **globally** without putting it in the YAML? (Hint: `ANSIBLE_ENABLE_TASK_DEBUGGER=True`).
3. Why is `strategy: free` **dangerous** with a debugger?
4. Does the debugger open a prompt on **each host** that fails, or just one?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): use the debugger to **fix a missing variable** at runtime and drop a file on `db1.lab`.

## 💡 Going further

- **`debugger: always`**: opens the REPL **after each task** (slow but useful in TDD).
- **`ANSIBLE_DISPLAY_TRACEBACK`** (2.18+): full Python traceback on exception.
- **Lab 91**: broken idempotence + tuning.
- **AAP**: no debugger, but `ansible-navigator replay` JSON artifacts.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/troubleshooting/debugger/lab.yml
ansible-lint labs/troubleshooting/debugger/challenge/solution.yml
ansible-lint --profile production labs/troubleshooting/debugger/challenge/solution.yml
```

> ⚠️ **Note**: `debugger:` is not flagged by ansible-lint but remains a
> **dev/debug** tool, never to leave in prod or CI/CD.
