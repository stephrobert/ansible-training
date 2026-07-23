# Lab 07 — Tags (targeting or ignoring a subset of tasks)

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

🔗 [**Ansible tags: targeting or ignoring a subset of tasks**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/tags/)

When a playbook grows (50, 100 tasks), you do not want to replay **everything** on each change. **Tags** are labels you place on tasks so you can **target** them at launch time:

```bash
ansible-playbook playbook.yml --tags install        # runs only the tasks tagged "install"
ansible-playbook playbook.yml --skip-tags database  # runs everything except "database"
```

Tags can be placed on a **task**, a **block**, an **entire play**, or a **role**. They are **inherited** from the container down to the children.

Special tags to know:

| Tag | Behavior |
| --- | --- |
| **`always`** | The task **always** runs, even if you filter `--tags other`. Exception: `--skip-tags always` cuts it. |
| **`never`** | The task **never runs**, unless you explicitly run `--tags <its tag>`. |
| **`tagged`** | Meta filter: runs only the tasks that have **at least one tag**. |
| **`untagged`** | Meta filter: runs only the tasks **with no tag at all**. |

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Place a **tag** on one task and on several tasks.
2. Target a subset with **`--tags`** and exclude with **`--skip-tags`**.
3. Inspect the execution plan without running anything (`--list-tags`, `--list-tasks`).
4. Use the special tag **`always`** for unavoidable tasks (logs, markers).
5. Use the special tag **`never`** for dangerous tasks (reset, drop).
6. Understand the **inheritance** of tags from a `block:` or a play.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ansible.builtin.ping
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
```

Expected response: `pong`. The second `ansible` cleans up the markers from previous runs.

## ⚙️ Target tree

```text
labs/ecrire-code/tags/
├── README.md           ← this file
├── playbook.yml        ← TO CREATE: your play with tags
└── challenge/
    ├── README.md       ← final challenge (already present)
    └── tests/
        └── test_*.py   ← (already present: pytest+testinfra)
```

## 📚 Exercise 1 — Playbook skeleton

Create `labs/ecrire-code/tags/playbook.yml` with 3 tasks that each drop a marker file:

```yaml
---
- name: Démo tags Ansible
  hosts: web1.lab
  become: true

  tasks:
    # Task 1: tagged install
    # Task 2: tagged configuration
    # Task 3: tagged service
```

🔍 **Observation**: a tag is just a `tags:` keyword added to a task. No constraint on the name: choose what describes the logical phase (`install`, `configuration`, `database`, `cleanup`…).

## 📚 Exercise 2 — Three tagged tasks

For each task, use `ansible.builtin.copy` with `content:`. Here is the first one as an example:

```yaml
- name: Marqueur stage install
  ansible.builtin.copy:
    dest: /tmp/tag-install.txt
    content: "install\n"
    mode: "0644"
  tags: install
```

> 💡 The content is **stable**. What a marker must prove here is that its task
> ran under a given tag filter: its **existence** proves it. Writing
> `{{ ansible_date_time.iso8601 }}` in it would make the task report `changed`
> on every pass, and you would lose idempotence without gaining anything. If you
> want to know *when* the marker was dropped, its `mtime` already tells you:
> `ls -l /tmp/tag-*.txt`.

Do the same for the tags `configuration` (dest = `/tmp/tag-configuration.txt`) and `service` (dest = `/tmp/tag-service.txt`).

🔍 **Observation to anticipate**: `tags:` accepts a **single value** (`tags: install`) or a **list** (`tags: [install, fast]`). Both forms are valid.

## 📚 Exercise 3 — Run **without a filter** (default case)

Without the `--tags` option, **all** the tasks run:

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml
```

🔍 **Observation**: `PLAY RECAP` shows `ok=4 changed=3` (the 3 tasks + the `gather_facts`). The 3 markers are dropped:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'ls /tmp/tag-*.txt'
# /tmp/tag-configuration.txt /tmp/tag-install.txt /tmp/tag-service.txt
```

## 📚 Exercise 4 — Target a single tag with `--tags`

Clean up the markers and rerun by **targeting** only `configuration`:

```bash
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags configuration
```

🔍 **Observation**: `PLAY RECAP` shows `ok=1 changed=1 skipped=2`. The `install` and `service` tasks are **skipped** (Ansible sees they do not have the requested tag).

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'ls /tmp/tag-*.txt'
# /tmp/tag-configuration.txt    ← only this file exists
```

## 📚 Exercise 5 — Exclude a tag with `--skip-tags`

The reverse of the previous one: everything, **except** `service`.

```bash
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
ansible-playbook labs/ecrire-code/tags/playbook.yml --skip-tags service
```

🔍 **Observation**: `install` and `configuration` run; `service` is skipped. In practice this is useful for "everything except the part that takes 10 min".

## 📚 Exercise 6 — Inspect without executing (`--list-tags`, `--list-tasks`)

Before running a long playbook with a filter, check that you are indeed targeting what you think:

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml --list-tags
```

🔍 **Observation**: expected output:

```text
play #1 (web1.lab): Démo tags Ansible    TAGS: []
    TASK TAGS: [configuration, install, service]
```

To see **which tasks** would be executed with a given filter:

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml --list-tasks --tags configuration
```

This is the equivalent of a **dry-run of the selection**, without running anything or connecting to the managed nodes.

## 📚 Exercise 7 — Special tag `always` (the unavoidable task)

Add a 4th task **before** the others, tagged `always`. It will serve as a universal marker: whatever filter is passed, it always runs.

```yaml
- name: Marqueur run (always)
  ansible.builtin.copy:
    dest: /tmp/tag-run.txt
    content: "run\n"
    mode: "0644"
  tags: always
```

Test it:

```bash
ansible web1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/tag-*.txt"
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags configuration
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'ls /tmp/tag-*.txt'
# /tmp/tag-configuration.txt /tmp/tag-run.txt    ← run.txt exists even though we filtered configuration!
```

🔍 **Observation**: `always` ignores the `--tags` filter. **Typical use case**: checking prerequisites, loading variables, dropping a run marker. Use it sparingly: a play full of `always` is a play with no useful tags.

## 📚 Exercise 8 — Special tag `never` (the dangerous task)

Add a 5th task tagged `[never, reset]` that removes all the markers:

```yaml
- name: Marqueur reset destructif
  ansible.builtin.shell: rm -f /tmp/tag-*.txt
  tags: [never, reset]
```

Test **two** scenarios:

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml                    # without a filter
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags configuration   # configuration filter
```

🔍 **Observation**: in **both cases**, the `reset` task is **skipped**. `never` is stronger than anything, except if you **explicitly** request its tag:

```bash
ansible-playbook labs/ecrire-code/tags/playbook.yml --tags reset
```

Only then does it run. **Typical use case**: destructive operations (drop database, file deletion, config reset) that you **never** want to see run by accident.

## 📚 Exercise 9 — Inheritance: a tag on a `block:`

Instead of repeating `tags: install` on 5 tasks, place it **once** on a `block:` that groups them:

```yaml
tasks:
  - name: Phase d'installation
    block:
      - name: Tâche 1 install
        ansible.builtin.copy:
          dest: /tmp/tag-install-1.txt
          content: "install 1\n"
          mode: "0644"

      - name: Tâche 2 install
        ansible.builtin.copy:
          dest: /tmp/tag-install-2.txt
          content: "install 2\n"
          mode: "0644"
    tags: install      # inherited by the block's 2 tasks
```

🔍 **Observation**: `--tags install` runs both tasks, even though neither has its own `tags:`. This is the **inheritance** rule: a tag on a container (block, play, role) is added to all the child tasks.

## 🔍 Observations to note

- A tag is **purely organizational**: it is just a label. No default behavior is associated with it (except the 4 special ones).
- **`--tags A,B`** runs the tasks tagged A **OR** B (union). **`--skip-tags A,B`** skips the tasks tagged A or B.
- **Inheritance** propagates from play → block → task. A task accumulates its own tags + the inherited ones.
- **`always`** = always except `--skip-tags always`. **`never`** = never except `--tags <its tag>`. No perfect symmetry: memorize it.
- **`--list-tags` and `--list-tasks`** are your friends before a long playbook. No need to connect to the managed nodes to use them.
- **Naming convention**: use short verbs/phases (`install`, `configure`, `deploy`, `cleanup`). Avoid generic tags (`tag1`, `important`) that help no one.

## 🤔 Reflection questions

1. You have 3 tags `install`, `configure`, `start`. You want to rerun **only** the configuration part **and** the service restart, **without** reinstalling. Which command?

2. You are writing a playbook that contains a task `Drop la base de production`. Which tag do you put on it so it **never** runs by accident, even if a colleague runs `--tags database`?

3. You want to run **only** the **untagged** tasks of a long playbook (audit / cleanup). Which special tag do you filter on?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) consolidates exercises 7 and 8 on `db1.lab`: an `always` task (marker), a standard `configuration` one, and a destructive `[never, reset]` task. Automated tests via `pytest+testinfra`:

```bash
pytest -v labs/ecrire-code/tags/challenge/tests/
```

## 💡 Going further

- **Tags per environment**: `tags: [prod, deploy]` on some tasks, `tags: [staging, deploy]` on others. Run `--tags "prod,deploy"` to target prod only.
- **Tags + `--check`**: `ansible-playbook playbook.yml --tags configure --check --diff`. This is the **filtered dry-run**: fast, safe, targeted. The ideal pattern in pre-prod.
- **Tags inherited from a role**: if you include a role with `roles: [{ role: webserver, tags: [web] }]`, **all** the role's tasks receive the `web` tag. One command, an entire role targeted.
- **`meta: end_play`** vs **`tags: never`**: `end_play` stops the play **conditionally** (with `when:`), `never` excludes **statically**. Choose depending on whether the decision is runtime or structural.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/tags/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/tags/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/tags/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
