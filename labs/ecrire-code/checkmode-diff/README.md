# Lab 08 — Check mode and diff (dry-run and visualization)

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

🔗 [**Ansible check mode and diff: dry-run and change visualization**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/checkmode-diff/)

`--check` simulates the execution without applying the changes. `--diff` shows the
unified diff of the modified files. `check_mode: false` at the task level forces a
real execution even in `--check` mode. Combined, these 3 tools are **the foundation of any
production operation**: you validate first, you apply next.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Run** a playbook in `--check` and read the `PLAY RECAP` correctly.
2. **Compare** the output of a real run vs a run in `--check --diff`.
3. **Identify** the modules that support `--check` and those that do not.
4. **Force** a task to run in `--check` via `check_mode: false`.
5. **Diagnose** a `changed=1` false positive in `--check` that would not have happened for real.

## 🔧 Preparation

Check that `web1.lab` is reachable and that you are at the repo root:

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
# Doit retourner "pong"
```

Make sure `/etc/motd` exists (by default on AlmaLinux, otherwise create an empty file):

```bash
ansible web1.lab -m command -a "ls -la /etc/motd" -b
```

## 📚 Exercise 1 — First `--check` on `copy:`

Create the `lab.yml` file at the root of the lab:

```yaml
---
- name: Lab checkmode - exercice 1
  hosts: web1.lab
  become: true
  tasks:
    - name: Poser un MOTD personnalise
      ansible.builtin.copy:
        dest: /etc/motd
        content: "Bienvenue sur web1 — Ansible RHCE 2026\n"
        mode: "0644"
```

**Run it in check mode**:

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check
```

Check **immediately after**:

```bash
ansible web1.lab -m command -a "cat /etc/motd"
```

🔍 **Observation**: the `PLAY RECAP` announces `changed=1`, but `cat /etc/motd` does
**not** show your new content. This is normal: `--check` is a dry-run, **nothing is
written** on the managed node side. The `changed=1` only indicates *what would have changed*.

## 📚 Exercise 2 — Add `--diff` to see the exact content

Rerun the same command with `--diff`:

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check --diff
```

🔍 **Observation**: the output now includes a **unified diff**:

```diff
--- before: /etc/motd
+++ after: /etc/motd
@@ -1 +1 @@
-Welcome to AlmaLinux 9
+Bienvenue sur web1 — Ansible RHCE 2026
```

This diff is **the raw material** of a change review before deployment.
In production, you **commit this diff in the PR** or send it to the Ops team before
launching for real.

**Now, real execution** (without `--check`):

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --diff
```

Check:

```bash
ansible web1.lab -m command -a "cat /etc/motd"
```

🔍 **Observation**: this time the content did change.

## 📚 Exercise 3 — Re-run in `--check` and compare

Rerun **immediately** the same command:

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check --diff
```

🔍 **Observation**: `PLAY RECAP` now announces `changed=0`, and **no diff**
is shown. This is **idempotence** combined with `--check`: Ansible compares the
local checksum to the checksum of the file on web1, they are identical, **no projected
change**.

**Practical implication**: a `--check` that outputs `changed=0` everywhere = nothing to apply.
This is the **steady state** you want to see in CI before a merge on `main`.

## 📚 Exercise 4 — `check_mode: false` for the tasks that need to run

Some tasks **must run** even in `--check`, because they produce
an **information** (not a change). Typical example: retrieving the version
of a binary with `command:`.

Modify `lab.yml`:

```yaml
---
- name: Lab checkmode - exercice 4
  hosts: web1.lab
  become: true
  tasks:
    - name: Recuperer la version d openssl (toujours executer)
      ansible.builtin.command: openssl version
      register: openssl_version
      check_mode: false
      changed_when: false

    - name: Afficher la version
      ansible.builtin.debug:
        var: openssl_version.stdout

    - name: Poser un MOTD avec la version d openssl
      ansible.builtin.copy:
        dest: /etc/motd
        content: "Web1 — openssl: {{ openssl_version.stdout }}\n"
        mode: "0644"
```

**Run in `--check`**:

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check --diff
```

🔍 **Observation**:

- The task `command: openssl version` **runs for real** (you see the version in the `debug:`).
- The task `copy:` **simulates** the write but does not write.
- The `--diff` shows the new value of the MOTD with the openssl version interpolated.

**Without `check_mode: false`** on the `command:` task, Ansible would have **skipped** the
retrieval of the version (and the rest of the playbook would have crashed with
`'openssl_version' is undefined` or a weird MOTD).

## 📚 Exercise 5 — The trap: modules that do not support `--check`

Not all modules **support** `--check` correctly. For unsupported modules,
Ansible shows a warning and **skips** the task in check mode.

Add to `lab.yml`:

```yaml
    - name: Tache non check-aware (exemple shell)
      ansible.builtin.shell: |
        echo "Hello from shell" >> /tmp/lab-shell-output.txt
```

**Rerun in `--check`**:

```bash
ansible-playbook labs/ecrire-code/checkmode-diff/lab.yml --check
```

🔍 **Observation**: the `shell:` task is marked **`skipped`** (not `changed`), with
a warning like `Skipping... unable to check_mode`. Ansible has no way to
guess what your shell command would do, so it refuses to simulate.

**Consequence**: in `--check`, you get **no** guarantee that the whole playbook
will run fine. The non check-aware `shell:` / `command:` tasks are **blind
spots**. To mitigate by:

- preferring **dedicated modules** (`copy:`, `template:`, `lineinfile:`) that are check-aware;
- adding `check_mode: false` + `changed_when: ...` to force the read-only execution.

## 🔍 Observations to note

Before moving on to the challenge, make sure you understand:

- **`--check` modifies nothing**, but the `PLAY RECAP` can show `changed=N` (change intent).
- **`--diff` is the review tool**: it is what appears in a change management PR.
- **`changed=0` in `--check`** = steady state, nothing to do in production.
- **`check_mode: false`** forces the execution of a task in check mode (useful for read-only tasks).
- **`shell:` / `command:`** are blind spots of `--check` unless you make them explicitly check-aware.

## 🤔 Reflection questions

1. You have a playbook that modifies an nginx config. You want to **validate the nginx
   syntax** before redeploying (via `nginx -t`). How do you combine `--check`,
   `check_mode: false`, and the `validate:` of the `template:` module to get a complete
   guarantee?

2. Why can a run in `--check` show `changed=1` while a real run
   immediately after will show `changed=0`? Give **two possible causes**.

3. In a CI, you run `ansible-playbook --check --diff` on every PR. What
   **exit code** does `ansible-playbook` return when `changed > 0` in `--check`?
   Should you **fail the CI** in that case?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Validation hooks**: combine the `validate:` of the `template:` module with `--check`
  to fail a dry-run if the generated config is syntactically invalid
  (`validate: 'nginx -t -c %s'`).
- **`--start-at-task`**: resume a playbook after a failed task, useful
  combined with `--check` to validate the rest before replaying.
- **The `audit-only` pattern**: a play that only does `command: changed_when: false`
  to collect info without modifying anything. Runs fine in `--check` because no
  task is supposed to modify the state.
- **`ANSIBLE_DIFF_ALWAYS=1`**: env variable to enable `--diff` by default
  without passing it on every command. Useful in local dev.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/checkmode-diff/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/checkmode-diff/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/checkmode-diff/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
