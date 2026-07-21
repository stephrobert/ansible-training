# Lab 39 — `cron:` module (schedule idempotent jobs)

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

🔗 [**Ansible cron module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-cron/)

`ansible.builtin.cron:` manages **cron jobs** with **idempotence guaranteed via the
`name:`**. Each job is identified by its **unique name** that Ansible writes as a
comment (`#Ansible: <name>`) above the job line. On every run, the
job is **updated** instead of being stacked.

The module can handle:

- the **user crontab** (`crontab -l`): default.
- the **`/etc/cron.d/*`** files via `cron_file:`: preferable for
  traceability.
- the **environment variables** (`MAILTO`, `PATH`) above the jobs (`env: true`).
- **disabling** without removal (`disabled: true`).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Understand** the `name:` mechanism and the `#Ansible:` marker.
2. **Choose** between the user crontab and `/etc/cron.d/` (and why the second is
   preferable).
3. **Define** environment variables (`MAILTO`, `PATH`) with `env: true`.
4. **Disable** a job without removing it (`disabled: true`).
5. **Use** the `special_time:` shortcuts (`hourly`, `daily`, etc.).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/cron.d/lab-rhce; crontab -u root -r 2>/dev/null; true"
```

## 📚 Exercise 1 — Job in the user crontab

Create `lab.yml`:

```yaml
---
- name: Demo cron crontab user
  hosts: db1.lab
  become: true
  tasks:
    - name: Backup quotidien dans la crontab de root
      ansible.builtin.cron:
        name: "Backup base de donnees"
        minute: "0"
        hour: "2"
        job: "/usr/local/bin/backup-db.sh > /var/log/backup.log 2>&1"
```

**Run**:

```bash
ansible-playbook labs/modules-services/cron/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo crontab -l'
```

🔍 **Observation**: root's crontab contains:

```text
#Ansible: Backup base de donnees
0 2 * * * /usr/local/bin/backup-db.sh > /var/log/backup.log 2>&1
```

**The `#Ansible: ...` comment** is the **idempotence marker**: Ansible
looks for this line on the next run to identify the job and replace it.

**Re-run**: `changed=0` (already in the right state).

## 📚 Exercise 2 — `/etc/cron.d/<file>` pattern (preferable)

```yaml
- name: Healthcheck dans /etc/cron.d/
  ansible.builtin.cron:
    name: "Healthcheck monitoring"
    minute: "*/5"
    job: "/usr/local/bin/healthcheck.sh"
    cron_file: monitoring
    user: root
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/cron.d/monitoring'
```

🔍 **Observation**: the `/etc/cron.d/monitoring` file is created. Important
differences with the user crontab:

| Characteristic | user crontab | `/etc/cron.d/<file>` |
|---|---|---|
| Visibility | `crontab -l -u root` (hidden) | `ls /etc/cron.d/` (visible) |
| Git versioning | No (system state) | Yes (file in `/etc/`) |
| Specifies `user:` per line | No (whole crontab of a user) | Yes (each line has a user) |
| Modularity | All jobs in 1 file | 1 file per module/role |

**Recommendation**: prefer **`cron_file:`** for **traceability** and
**modularity**.

## 📚 Exercise 3 — Environment variables (`env: true`)

```yaml
- name: Definir MAILTO pour les jobs lab
  ansible.builtin.cron:
    name: MAILTO
    env: true
    value: admin@lab.local
    cron_file: lab-rhce
    user: root

- name: Definir PATH custom (binaires myapp)
  ansible.builtin.cron:
    name: PATH
    env: true
    value: /opt/myapp/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
    cron_file: lab-rhce
    user: root

- name: Job qui utilise les vars
  ansible.builtin.cron:
    name: "Backup horaire"
    minute: "0"
    job: "myapp-backup.sh"  # Resolved via PATH
    cron_file: lab-rhce
    user: root
```

🔍 **Observation**:

- **`env: true`** changes the semantics: `name:` becomes the **variable name**,
  `value:` is its **value**.
- **Useful variables**: `MAILTO`, `PATH`, `SHELL`.

**Check the generated file**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/cron.d/lab-rhce'
```

```text
#Ansible: MAILTO
MAILTO="admin@lab.local"
#Ansible: PATH
PATH="/opt/myapp/bin:/usr/local/sbin:..."
#Ansible: Backup horaire
0 * * * * root myapp-backup.sh
```

**`PATH`** is crucial: by default, cron's `PATH` is **very restrictive**
(`/usr/bin:/bin`). If your script is in `/opt/myapp/bin/`, it will **not
be found** without this `PATH:` override.

## 📚 Exercise 4 — Disable a job without removing it

```yaml
- name: Suspendre temporairement le backup horaire
  ansible.builtin.cron:
    name: "Backup horaire"
    minute: "0"
    job: "myapp-backup.sh"
    cron_file: lab-rhce
    user: root
    disabled: true
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cat /etc/cron.d/lab-rhce'
```

```text
#Ansible: Backup horaire
#0 * * * * root myapp-backup.sh
```

🔍 **Observation**: the job line is **commented out** (`#0 * * * * ...`). The job
**no longer runs** but stays **kept for reference**. To **re-enable** it,
set `disabled: false` again.

**Use case**: scheduled maintenance, debugging a crashing script,
suspending a cron during an audit.

## 📚 Exercise 5 — `special_time:` (shortcuts)

```yaml
- name: Job hourly avec raccourci
  ansible.builtin.cron:
    name: "Healthcheck rapide"
    special_time: hourly
    job: "/usr/local/bin/healthcheck.sh"
    cron_file: lab-rhce
    user: root
```

| Form | Equivalent | Usage |
|---|---|---|
| `special_time: hourly` | `0 * * * *` | Every hour |
| `special_time: daily` | `0 0 * * *` | Every day at midnight |
| `special_time: weekly` | `0 0 * * 0` | Every Sunday at midnight |
| `special_time: monthly` | `0 0 1 * *` | The 1st of each month |
| `special_time: reboot` | `@reboot` | At every startup |

🔍 **Observation**: `special_time:` **excludes** the `minute/hour/day/month/weekday` options.
Use **either** `special_time:` **or** the others, not both.

## 📚 Exercise 6 — Removing a job (`state: absent`)

```yaml
- name: Supprimer le job "Backup horaire"
  ansible.builtin.cron:
    name: "Backup horaire"
    state: absent
    cron_file: lab-rhce
    user: root
```

🔍 **Observation**: Ansible looks for the `#Ansible: Backup horaire` comment and
**removes that line + the job line just below it**.

**Important**: without `state: absent`, a **renamed** or **moved** job becomes
**orphaned** in the crontab. Always **do the explicit cleanup** when you
restructure the jobs.

## 📚 Exercise 7 — The trap: changing the `name:` stacks instead of replacing

```yaml
# Run 1
- ansible.builtin.cron:
    name: "Backup BDD"
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/backup-db.sh"

# Run 2 (after RENAMING)
- ansible.builtin.cron:
    name: "Backup base de donnees"  # New name
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/backup-db.sh"  # Same job
```

🔍 **Observation**: the crontab contains **2 identical jobs**! One with
`#Ansible: Backup BDD`, the other with `#Ansible: Backup base de donnees`. The job
will run **twice** at 2 a.m.

**Solution**: before renaming, **remove the old one**:

```yaml
- ansible.builtin.cron:
    name: "Backup BDD"  # Old name
    state: absent

- ansible.builtin.cron:
    name: "Backup base de donnees"  # New name
    minute: "0"
    hour: "2"
    job: "/usr/local/bin/backup-db.sh"
```

**Rule**: `name:` is the **identification key**. **Never** change it
without a migration plan.

## 🔍 Observations to note

- **`name:`** = idempotence key. **Never** change it after creation.
- **`cron_file:` in `/etc/cron.d/`** is preferable to the user crontab (visibility, versioning).
- **`env: true`** for `MAILTO`, `PATH`, `SHELL`: not in the same task as the jobs.
- **`disabled: true`** disables without removing: useful for maintenance.
- **`special_time:`** shortens common schedules: excludes the
  `minute/hour/etc` options.
- **`state: absent`** + `name:` = remove a job (with its marker comment).

## 🤔 Reflection questions

1. You manage 5 different cron jobs for the `monitoring` role. You want
   to be able to **deploy/remove** all these jobs in a single pass. Which pattern
   (`cron_file:`, `loop:`, ...)?

2. Why is `PATH` in the crontab a classic trap for custom
   scripts? What is the default value of cron's `PATH`?

3. You want to run a script **every 30 minutes** but also **at
   every reboot**. How do you articulate two `cron:` tasks (with and without
   `special_time:`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`hour: "8-18"`** or **`hour: "*/2"`**: ranges and steps in the schedules.
- **`at:` pattern**: for **one-off jobs** (not recurring): the
  `ansible.posix.at` module (ansible.posix collection).
- **Anacron**: for jobs that must **catch up** their missed runs if
  the machine was off. Not handled directly by Ansible `cron:`: go
  through `template:` on `/etc/cron.daily/`.
- **systemd timers**: modern alternative to cron, more powerful (multiple
  triggers, dependencies). Managed via `systemd_service:` on the `.timer` units.
- **`audit cron` pattern**: a play that collects all crontabs of all
  hosts via `command: crontab -l` + `fetch:`: for centralized audit.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-services/cron/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-services/cron/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-services/cron/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
