# Schedule the backup and the cleanup that never ran

## The situation

The `/tmp` partition on **db1.lab** filled up on Sunday and took the database
down with it, while the hourly backup everyone assumed was running turned out
to live in nobody's crontab. Both jobs must be scheduled, and above all
**auditable**: the previous admin edited a shared crontab by hand, and no one
can tell today who added what. You are switching to a dedicated, versioned file
deployed from **control-node.lab**, and failures must reach a human.

Your mission:

1. Provision a **file of your own under `/etc/cron.d/`** on **db1.lab**, rather
   than patching the shared crontab, so a role owns its schedule.
2. Set the **notification address** at the top of that file, so a failing job
   mails someone instead of dying in silence.
3. Schedule the two jobs as root: the **hourly backup** and the **daily 3 a.m.
   cleanup** of files older than a week in `/tmp`.
4. Guarantee **idempotence**: replaying the playbook must not stack a second
   copy of each job.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-cron/ (in French)

## 🎯 Challenge — `cron:` module (2 jobs via `cron_file:`)

### ✅ Objective

On **db1.lab**, create a dedicated file **`/etc/cron.d/lab-rhce`** that
contains:

- An environment variable `MAILTO=admin@lab.local`
- **Job 1**: `Backup horaire` at `0 * * * *` (minute 0 of every hour),
  runs `/usr/local/bin/backup.sh` as `root`.
- **Job 2**: `Cleanup quotidien` at `0 3 * * *` (3 a.m.),
  runs `/usr/bin/find /tmp -mtime +7 -delete` as `root`.

> 💡 **Why `cron_file:` rather than the user crontab?**
> `/etc/cron.d/<file>` is versioned via Ansible, directly readable,
> and lets you lay down a **packageable configuration** (a role drops its
> dedicated file, which is cleaner than patching a shared crontab).

### 🧩 `cron_file:` pattern

With `cron_file: lab-rhce`, **each call** to `ansible.builtin.cron`
writes/modifies a line in `/etc/cron.d/lab-rhce`. So that
Ansible recognizes an already-placed line and does not duplicate it, it uses
the `name:` (which becomes a `#Ansible: <name>` comment in the file).

> ⚠️ **`name:`** is **mandatory** when you use `cron_file:`:
> it is the idempotence identifier.

### 🧩 Skeleton

```yaml
---
- name: Challenge - cron via fichier dédié
  hosts: db1.lab
  become: true

  tasks:
    - name: Variable d'environnement MAILTO
      ansible.builtin.cron:
        name: ???
        env: ???
        value: ???
        cron_file: ???
        user: root

    - name: Job backup horaire
      ansible.builtin.cron:
        name: ???
        minute: ???
        # hour: defaults to "*"
        job: ???
        cron_file: ???
        user: root

    - name: Job cleanup quotidien
      ansible.builtin.cron:
        name: ???
        minute: ???
        hour: ???
        job: ???
        cron_file: ???
        user: root
```

> 💡 **Traps**:
>
> - **`name:`** is the **idempotence marker** (`#Ansible: <name>`
>   comment in the crontab). Without it, each run adds a new entry.
> - **`cron_file:`** creates `/etc/cron.d/<file>` (system-wide). Without it,
>   it modifies the user crontab (`/var/spool/cron/<user>`).
> - **`user:`**: for `cron_file:`, it is the user that runs the task
>   (field between minute and command). For the user crontab, it is the crontab
>   targeted.
> - **`@reboot`** as `special_time:`: `special_time: reboot`,
>   `daily`, `weekly`, etc. Avoids the manual writing of
>   `0 0 * * 0`.

### 🚀 Run

```bash
ansible-playbook labs/modules-services/cron/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/cron.d/lab-rhce"
```

🔍 Expected output (excerpt):

```text
#Ansible: MAILTO
MAILTO=admin@lab.local
#Ansible: Backup horaire
0 * * * * root /usr/local/bin/backup.sh
#Ansible: Cleanup quotidien
0 3 * * * root /usr/bin/find /tmp -mtime +7 -delete
```

### 🧪 Automated validation

```bash
pytest -v labs/modules-services/cron/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-services-cron
```

### 💡 Going further

- **User crontab**: without `cron_file:`, `cron:` modifies the crontab of
  the target user (`crontab -e`). More standard but less versionable.
- **`special_time:`**: shortcut for `@reboot`, `@hourly`, `@daily`,
  `@weekly`, `@monthly`.
- **`disabled: true`**: comments out the line (instead of removing it). Lets
  you temporarily disable a job without losing its definition.
- **Lint**:

   ```bash
   ansible-lint labs/modules-services/cron/challenge/solution.yml
   ```
