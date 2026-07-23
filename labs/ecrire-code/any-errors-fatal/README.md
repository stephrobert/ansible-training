# Lab 26 — `any_errors_fatal:` (stop the play on the 1st error)

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

🔗 [**Ansible any_errors_fatal: stop the play on the 1st cluster error**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/any-errors-fatal/)

By default, Ansible **continues** the play on the other hosts if **one** host fails.
`any_errors_fatal: true` changes this behavior: **as soon as the first error occurs**, the
play **stops on all hosts**, even those that have not started yet.

It is the exact opposite of `ignore_errors: true`. Use case: **transactional cluster**
operations that must succeed everywhere or nowhere (provisioning
a Galera cluster, configuring an etcd quorum, deploying a database schema).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Enable** `any_errors_fatal: true` at the play level.
2. **Compare** with the default behavior on 2+ hosts.
3. **Distinguish** `any_errors_fatal: true` from `max_fail_percentage: 0`.
4. **Combine** with `serial:` for "one fails → all stop" patterns.
5. **Choose** between `any_errors_fatal:` and `block/rescue` depending on the scenario.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible webservers -m ping
ansible webservers -b -m shell -a "rm -f /tmp/aef-*.txt"
```

## 📚 Exercise 1 — Default behavior (without `any_errors_fatal`)

Create `lab.yml`:

```yaml
---
- name: Demo defaut sans any_errors_fatal
  hosts: webservers
  become: true
  tasks:
    - name: Tache 1 - poser un marqueur
      ansible.builtin.copy:
        content: "tache 1 OK\n"
        dest: /tmp/aef-task1.txt
        mode: "0644"

    - name: Tache 2 - echec UNIQUEMENT sur web1
      ansible.builtin.command: /bin/false
      when: inventory_hostname == 'web1.lab'

    - name: Tache 3 - poser un autre marqueur
      ansible.builtin.copy:
        content: "tache 3 OK\n"
        dest: /tmp/aef-task3.txt
        mode: "0644"
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/any-errors-fatal/lab.yml
```

🔍 **Observation**:

- web1: task 1 OK → task 2 **crashes** → web1 is **removed** from the play.
- web2: task 1 OK → task 2 **skipped** (not web1) → task 3 OK.

PLAY RECAP: `web1: failed=1`, `web2: ok=2`. **Web2 kept going** while web1
was crashing.

```bash
ansible webservers -b -m command -a "ls /tmp/aef-task*.txt"
```

**On web1**: only `aef-task1.txt`. **On web2**: `aef-task1.txt` AND
`aef-task3.txt`.

## 📚 Exercise 2 — With `any_errors_fatal: true`

Modify the play:

```yaml
- name: Demo any_errors_fatal
  hosts: webservers
  become: true
  any_errors_fatal: true
  tasks:
    - ...  # meme tasks
```

**Reset, then run**:

```bash
ansible webservers -b -m shell -a "rm -f /tmp/aef-*.txt"
ansible-playbook labs/ecrire-code/any-errors-fatal/lab.yml
```

🔍 **Observation**:

- web1: task 1 OK → task 2 **crashes**.
- web2: task 1 OK → task 2 skipped → **task 3 NOT executed** because the play
  stops.

PLAY RECAP: `web1: ok=1 failed=1`, `web2: ok=1 failed=0`. **web2 is not marked
failed** — it crashed on nothing. What proves the halt is its `ok` counter:
**1 instead of 2**, because task 3 never ran. Compare with the previous run,
where web2 ended at `ok=2`.
**The whole play is failed**.

```bash
ansible webservers -b -m command -a "ls /tmp/aef-task*.txt"
```

**Web2**: only `aef-task1.txt`. Task 3 did not run. This is the
`any_errors_fatal:` effect.

## 📚 Exercise 3 — When to use `any_errors_fatal: true`

Typical use cases where **you do not want to continue**:

1. **Configuring a cluster**: if 1 node fails to receive the certificate, **nothing**
   must be configured on the others (otherwise you end up with a broken cluster).
2. **Provisioning a quorum** (etcd, Consul): if 1 node fails, the quorum is
   compromised, so you may as well stop everything and investigate.
3. **Deploying a DB schema**: the migration on the primary fails → the
   replicas must **absolutely not** apply the partial migration.

```yaml
- name: Migration DB cluster (atomique)
  hosts: db_cluster
  any_errors_fatal: true
  tasks:
    - name: Backup avant migration
      ansible.builtin.command: pg_dump ...

    - name: Appliquer la migration
      ansible.builtin.command: psql -f /tmp/migration.sql
```

If the backup fails on 1 node → **you do not attempt** the migration on the others.

## 📚 Exercise 4 — `any_errors_fatal:` vs `max_fail_percentage:`

`max_fail_percentage:` is more **fine-grained**: it accepts a certain percentage of failure
before aborting.

```yaml
- name: Tolerance 20% d echec
  hosts: webservers
  serial: 5
  max_fail_percentage: 20
  tasks:
    - ...
```

| Directive | Effect |
|---|---|
| None | Continues on the hosts that work |
| `any_errors_fatal: true` | Stops on the **1st** error |
| `max_fail_percentage: 0` | Same as `any_errors_fatal: true` |
| `max_fail_percentage: 20` | Stops if **>20%** failed in the batch |
| `max_fail_percentage: 50` | Tolerates up to 50% failure |

🔍 **Observation**: `any_errors_fatal: true` is **equivalent to `max_fail_percentage: 0`**
for strict behavior. Prefer `max_fail_percentage:` to get fine-grained
control.

## 📚 Exercise 5 — Combining `any_errors_fatal:` + `block/rescue`

Question: if a task in a `block/rescue` fails but the `rescue:` catches it,
does `any_errors_fatal:` trigger?

**Answer**: **No**. `any_errors_fatal:` only triggers on **uncaught
errors**.

```yaml
- name: Demo any_errors_fatal + block/rescue
  hosts: webservers
  any_errors_fatal: true
  tasks:
    - block:
        - name: Tache qui plante
          ansible.builtin.command: /bin/false
      rescue:
        - name: Rescue local
          ansible.builtin.debug:
            msg: "Rattrape"

    - name: Cette tache tourne quand meme
      ansible.builtin.debug:
        msg: "any_errors_fatal pas declenche"
```

🔍 **Observation**: the rescue **catches** the `/bin/false` task, so
`any_errors_fatal:` **is not triggered** and the play continues. This is the desirable
behavior: `any_errors_fatal:` only triggers on **unhandled errors**.

## 📚 Exercise 6 — The trap: `any_errors_fatal:` + `unreachable` task

`unreachable` (host unreachable, SSH down) is handled **differently** depending on the
Ansible versions.

On recent Ansible 2.x, `any_errors_fatal: true` **includes** `unreachable`:
if web1 becomes unreachable during the play, `any_errors_fatal:` triggers the stop.

On older versions (before 2.x), you had to combine it with
`max_fail_percentage:` to handle `unreachable`.

🔍 **Observation**: test which version you have with `ansible --version`. On
Ansible Core 2.20 (RHEL 10), `any_errors_fatal:` does cover `unreachable`.

## 🔍 Observations to note

- **Default behavior**: Ansible continues on the surviving hosts when a failure occurs.
- **`any_errors_fatal: true`** at the play level = **stop on the 1st error** on all hosts.
- **`max_fail_percentage: N`** = fine-grained tolerance (`0` is equivalent to `any_errors_fatal: true`).
- **Block/rescue catches before `any_errors_fatal:`**, so no stop if the rescue is OK.
- **Use case**: atomic cluster operations (DB cluster, quorum, certificates).
- **Anti-pattern**: `any_errors_fatal: true` on an audit play (you stop everything
  for 1 host that did not have the package, which makes no sense).

## 🤔 Reflection questions

1. You deploy to 100 webservers with `serial: 10`. You want to abort if **more
   than 10%** of a batch fails. Which directive: `any_errors_fatal: true`,
   `max_fail_percentage: 10`, or both?

2. Why is `any_errors_fatal: true` **dangerous** on a **multi-host audit**
   play?

3. How do you combine `any_errors_fatal: true` + `block/rescue` to get an
   "abort unless we explicitly catch" behavior?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`max_fail_percentage:` + `serial:`** = **canary deploy with
  circuit-breaker** pattern. See lab 09.
- **Difference with `force_handlers:`**: `any_errors_fatal:` stops everything, but
  the **handlers already notified** continue by default. With `force_handlers: true`,
  you guarantee that the handlers run even when an abort occurs.
- **`fail` module + `any_errors_fatal:`**: equivalent to a cluster `assert:`. If
  a condition is not satisfied on 1 host, you abort the play.
- **`health-check play first` pattern**: a first `any_errors_fatal: true` play
  that checks all the prerequisites, followed by the real deployment play. If the health-check
  fails, nothing is deployed.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/any-errors-fatal/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/any-errors-fatal/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/any-errors-fatal/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
