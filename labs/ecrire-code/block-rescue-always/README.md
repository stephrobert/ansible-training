# Lab 23 — `block:` / `rescue:` / `always:` (try / catch / finally)

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

🔗 [**Block / rescue / always Ansible: try/catch/finally**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/block-rescue-always/)

`block:` groups several tasks under an **error-handling structure**:

- **`block:`** = list of tasks to try (equivalent of `try`).
- **`rescue:`** = list of tasks run **if a task in the block fails** (`catch`).
- **`always:`** = list of tasks **always** run, on success or failure (`finally`).

This structure is essential for **transactional operations**: deploy
a new release, back up in case of failure, clean up a temporary file.
Without `block/rescue`, a `failed_when` can break the whole play: with
`block/rescue`, you catch cleanly.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Group** several tasks in a `block:`.
2. **Catch** an error with `rescue:` and **act** (rollback, notification, log).
3. **Guarantee** a cleanup with `always:`.
4. **Use** `ansible_failed_task` and `ansible_failed_result` in `rescue:`.
5. **Nest** blocks for complex try/catch/finally structures.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/block-*.txt"
```

## 📚 Exercise 1 — Block without error (nominal case)

Create `lab.yml`:

```yaml
---
- name: Demo block sans erreur
  hosts: db1.lab
  become: true
  tasks:
    - name: Block transactionnel
      block:
        - name: Tache 1 - Marquer le debut
          ansible.builtin.copy:
            content: "Start at {{ ansible_date_time.iso8601 }}\n"
            dest: /tmp/block-start.txt
            mode: "0644"

        - name: Tache 2 - Operation principale
          ansible.builtin.copy:
            content: "Main operation OK\n"
            dest: /tmp/block-main.txt
            mode: "0644"

      rescue:
        - name: Rescue (ne devrait PAS tourner ici)
          ansible.builtin.copy:
            content: "Erreur capturee !\n"
            dest: /tmp/block-rescue.txt
            mode: "0644"

      always:
        - name: Always - cleanup
          ansible.builtin.copy:
            content: "Cleanup at {{ ansible_date_time.iso8601 }}\n"
            dest: /tmp/block-cleanup.txt
            mode: "0644"
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/lab.yml
```

🔍 **Observation**: console output:

```
TASK [Tache 1 - Marquer le debut] : ok / changed
TASK [Tache 2 - Operation principale] : ok / changed
TASK [Always - cleanup] : ok / changed
```

**`rescue:` is not run**. **`always:` is run**. On db1:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'ls /tmp/block-*.txt'
# block-cleanup.txt, block-main.txt, block-start.txt — PAS block-rescue.txt
```

## 📚 Exercise 2 — Block with error (triggering `rescue:`)

Modify **Task 2** so that it fails:

```yaml
- name: Tache 2 - Operation qui plante
  ansible.builtin.dnf:
    name: paquet-inexistant-12345
    state: present
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/lab.yml
```

🔍 **Observation**: console output:

```
TASK [Tache 1 - Marquer le debut] : ok / changed
TASK [Tache 2 - Operation qui plante] : FAILED!
TASK [Rescue ...] : ok / changed
TASK [Always - cleanup] : ok / changed
```

**`rescue:` is run** (task 2 failed). **`always:` is run too**.
The **PLAY RECAP** shows `failed=0` because the `rescue:` **caught** the error: the
play ends **successfully**.

This is the **equivalent of Python's `try/except`**: without `rescue:`, task 2 would have
done `failed=1` and stopped the play.

## 📚 Exercise 3 — Magic variables in `rescue:`

In `rescue:`, Ansible exposes **two** very useful **variables**:

- **`ansible_failed_task`**: the dict of the task that failed (`name`, `action`, ...).
- **`ansible_failed_result`**: the result of the task (msg, rc, stderr, ...).

```yaml
rescue:
  - name: Diagnostiquer l erreur
    ansible.builtin.copy:
      dest: /tmp/block-rescue-diagnostic.txt
      mode: "0644"
      content: |
        Tache echouee : {{ ansible_failed_task.name }}
        Module : {{ ansible_failed_task.action }}
        Message : {{ ansible_failed_result.msg | default('inconnu') }}
        Stderr : {{ ansible_failed_result.stderr | default('') }}

  - name: Notifier (simulation)
    ansible.builtin.debug:
      msg: "ALERTE : tache '{{ ansible_failed_task.name }}' a echoue sur {{ inventory_hostname }}"
```

🔍 **Observation**: these variables allow a **targeted rescue**: precise log,
structured notification, conditional branching depending on the error.

## 📚 Exercise 4 — `always:` for transactional cleanup

Classic pattern: create a temporary file, do the operation, **always**
remove it (on success or failure).

```yaml
- name: Operation transactionnelle avec cleanup garanti
  hosts: db1.lab
  become: true
  tasks:
    - name: Block transactionnel avec cleanup
      block:
        - name: Creer un fichier de lock
          ansible.builtin.copy:
            content: "PID {{ ansible_date_time.epoch }}\n"
            dest: /tmp/block-lock.txt
            mode: "0644"

        - name: Operation critique (peut echouer)
          ansible.builtin.command: /bin/false
          # Tache qui plante volontairement

      rescue:
        - name: Logger l echec
          ansible.builtin.copy:
            content: "Echec rattrape\n"
            dest: /tmp/block-fail-log.txt
            mode: "0644"

      always:
        - name: Toujours supprimer le lock
          ansible.builtin.file:
            path: /tmp/block-lock.txt
            state: absent
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/lab.yml
```

🔍 **Observation**: `block-lock.txt` is **created then removed**. Even if the critical
operation fails, the lock is cleaned up. This is the essential **transactional pattern**
to avoid orphan locks.

## 📚 Exercise 5 — Nested block (complex try / catch / finally)

```yaml
- name: Block externe
  block:
    - name: Block interne 1
      block:
        - name: Operation interne
          ansible.builtin.command: /bin/false
      rescue:
        - name: Rescue interne
          ansible.builtin.debug:
            msg: "Rescue interne capture"

    - name: Tache apres le rescue interne
      ansible.builtin.debug:
        msg: "Cette tache tourne car le rescue interne a rattrape"

  rescue:
    - name: Rescue externe (ne devrait PAS tourner)
      ansible.builtin.debug:
        msg: "Rescue externe"

  always:
    - name: Always externe
      ansible.builtin.debug:
        msg: "Always externe"
```

🔍 **Observation**: the **inner rescue** catches the error, so the **outer rescue
is not triggered**. A pattern useful for **cascading fallbacks**: try A,
if A fails try B, if B fails then notify.

## 📚 Exercise 6 — The trap: a `rescue:` that also fails

If a task in the `rescue:` **fails itself**, the `rescue` does **not** catch
its own error: the play stops.

```yaml
- name: Demo piege rescue qui plante
  block:
    - ansible.builtin.command: /bin/false  # Tache 1 plante

  rescue:
    - ansible.builtin.command: /bin/false  # Rescue plante aussi

  always:
    - ansible.builtin.debug:
        msg: "Always tourne quand meme"
```

🔍 **Observation**: the **rescue fails**, the **always runs anyway**, but the
PLAY RECAP shows `failed=1`. The play has failed. The rescue does not **catch
its own error**.

**Good practice**: a `rescue:` must be **simple and reliable** (a notification,
a log, a cleanup): do not put operations in it that can themselves fail.

## 🔍 Observations to note

- **`block:`** = try, **`rescue:`** = catch, **`always:`** = finally.
- **`rescue:` catches the errors** of the block and prevents the play from failing.
- **`always:`** runs **always**, on success or failure.
- **`ansible_failed_task` / `ansible_failed_result`** = magic variables in `rescue:`.
- **Nested blocks** = cascading fallbacks.
- **A `rescue:` that fails** does not catch its own error: the `always:` runs but the play fails.

## 🤔 Reflection questions

1. You want to **deploy a release** with automatic rollback in case of failure.
   How do you articulate `block:` (deploy), `rescue:` (rollback), and `always:`
   (notification)?

2. What is the semantic difference between `ignore_errors: true` (single task)
   and `block: + rescue:` (group of tasks)? When do you prefer one over the other?

3. A `rescue:` can **modify** variables with `set_fact`. How do you check
   after the block whether the run went through the `rescue:` (to condition a
   later task)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`when:` on a block**: conditions the whole block, equivalent to putting
  `when:` on each task, but DRY.
- **`tags:` on a block**: applies the tag to all the tasks of the block. Useful
  for tagged "deploy" / "rollback" / "verify" sections.
- **`become:` on a block**: elevates privileges for all the tasks of the block,
  cleaner than repeating `become: true` on each task.
- **Saga pattern**: chain several transactional blocks with their own
  rescue. If one fails, trigger the compensations of the previous ones (cascading
  rollback).
- **Lab 25 (`ignore_errors`)**: a simpler alternative when you just want to **not
  crash** without handling the catch.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/block-rescue-always/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/block-rescue-always/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/block-rescue-always/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
