# Lab 10 — Async and poll (long tasks without blocking SSH)

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

🔗 [**Async and poll Ansible: long tasks, fire-and-forget, async_status**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/async-poll/)

By default, Ansible **keeps an SSH connection open** for the entire duration
of a task. If the task lasts 30 minutes, you risk an **SSH timeout** (network that
drops, firewall that kills idle connections): Ansible then loses the output and
considers the task **failed** while it keeps running on the managed node.

`async:` detaches the task from the Ansible process and **frees the SSH connection**.
`poll:` controls whether Ansible waits (`> 0`) or not (`0` = fire-and-forget). To
retrieve the result later, `async_status:` queries the **job ID**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Detach** a long task with `async + poll: 0` (fire-and-forget).
2. **Retrieve** the result later via `async_status: jid:`.
3. **Combine** `async:` with `until:` to do active polling.
4. **Diagnose** an orphan job (the process is gone, but we lost the `jid`).
5. **Choose** between `async + poll > 0` (sync with heartbeat) and `async + poll: 0` (truly async).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
```

## 📚 Exercise 1 — The problem: a long task that times out

To understand the point of `async`, first observe what happens **without** it.
Create `lab-blocking.yml`:

```yaml
---
- name: Tache longue sans async (problematique)
  hosts: web1.lab
  become: true
  tasks:
    - name: Sleep 5 secondes
      ansible.builtin.command: sleep 5
```

**Run it and time it**:

```bash
time ansible-playbook labs/ecrire-code/async-poll/lab-blocking.yml
```

🔍 **Observation**: the play takes **5+ seconds** to finish, and the SSH connection stays
**open** the whole time. On a 5s sleep no problem: on a 30-minute task over a VPN
that cuts idle sessions at 5 min, it is a disaster.

## 📚 Exercise 2 — Async with `poll: 0` (fire-and-forget)

Create `lab-async.yml`:

```yaml
---
- name: Demo async + async_status
  hosts: web1.lab
  become: true
  tasks:
    - name: Lancer sleep 8 en background (fire-and-forget)
      ansible.builtin.command: sleep 8
      async: 30      # Timeout cote managed node
      poll: 0        # Ne pas bloquer Ansible
      register: sleep_job

    - name: Afficher le job ID retenu
      ansible.builtin.debug:
        msg: "Job lance avec ID {{ sleep_job.ansible_job_id }}"

    - name: Attendre la fin du job async
      ansible.builtin.async_status:
        jid: "{{ sleep_job.ansible_job_id }}"
      register: job_result
      until: job_result.finished
      retries: 15
      delay: 2

    - name: Afficher le statut final
      ansible.builtin.debug:
        msg: "Job {{ sleep_job.ansible_job_id }} fini en {{ job_result.delta }}"
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/async-poll/lab-async.yml
```

🔍 **Observation**:

- The `Lancer sleep 8` task returns **immediately** (the SSH connection closes).
- `async_status` polls every 2 seconds (`delay: 2`) up to 15 times (`retries: 15` = max 30s).
- When the sleep finishes on the managed node, `async_status` returns `finished: 1`.

**Why not just `poll > 0`?** With `async: 30` and `poll: 5`, Ansible polls
**every 5 seconds** but **keeps the connection open** between two polls. Ideal
for **medium** tasks (10-60s). With `poll: 0`, the connection is **closed
immediately**: ideal for **really long** tasks (>5min).

## 📚 Exercise 3 — Several jobs in parallel on the same host

`async + poll: 0` lets you **launch N concurrent jobs** on a single host. Very useful
to, for example, parallelize several `dnf install` commands or
multi-file downloads.

Create `lab-parallel.yml`:

```yaml
---
- name: Lancer 3 jobs en parallele
  hosts: web1.lab
  become: true
  tasks:
    - name: Job 1 - sleep 4
      ansible.builtin.command: sleep 4
      async: 30
      poll: 0
      register: job1

    - name: Job 2 - sleep 6
      ansible.builtin.command: sleep 6
      async: 30
      poll: 0
      register: job2

    - name: Job 3 - sleep 8
      ansible.builtin.command: sleep 8
      async: 30
      poll: 0
      register: job3

    - name: Attendre la fin des 3 jobs
      ansible.builtin.async_status:
        jid: "{{ item }}"
      register: jobs_result
      until: jobs_result.finished
      retries: 20
      delay: 1
      loop:
        - "{{ job1.ansible_job_id }}"
        - "{{ job2.ansible_job_id }}"
        - "{{ job3.ansible_job_id }}"
```

**Run it and time it**:

```bash
time ansible-playbook labs/ecrire-code/async-poll/lab-parallel.yml
```

🔍 **Observation**: the whole play takes ~**8 seconds** (the duration of the longest job),
not 4+6+8 = 18s. The 3 jobs ran **in parallel** on the managed node.

## 📚 Exercise 4 — The trap: `async: <T>` shorter than the task

Modify exercise 2 so that `async: 5` but the sleep is `sleep 8`:

```yaml
- name: Lancer sleep 8 avec async timeout 5
  ansible.builtin.command: sleep 8
  async: 5    # Timeout cote managed node — INSUFFISANT
  poll: 0
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/async-poll/lab-async.yml
```

🔍 **Observation**: `async_status` ends up returning `finished: 1` BUT with a
**`failed: 1`** and a message `async task did not complete within the requested time`.

This is the **managed-node-side timeout**: Ansible (actually the `async_wrapper` helper)
**kills** the process if the task exceeds `async:` seconds.

**Rule**: `async:` must be **always greater** than the maximum expected duration
of the task, with a generous margin (×2 or ×3).

## 📚 Exercise 5 — Orphan job (true fire-and-forget)

`async + poll: 0` **without** `async_status:` launches a job that you **never wait for**.
Handy to trigger something whose result you do not care about in
this play (notification, metrics push, etc.).

```yaml
- name: Notifier Slack en arriere-plan (on s en fout du resultat)
  ansible.builtin.command: |
    curl -X POST -H 'Content-type: application/json'
    --data '{"text":"deploy done on {{ inventory_hostname }}"}'
    https://hooks.slack.com/services/...
  async: 60
  poll: 0
  changed_when: false
```

🔍 **Observation**: Ansible **does not know** whether the curl succeeded. If the Slack API is
down, you lose the notification but the deploy continues. This is **acceptable** for
best-effort notifications.

**Warning**: for a **critical operation** (database insert, backup
generation), **never** do fire-and-forget without `async_status:`: you lose the
visibility of errors.

## 🔍 Observations to note

- **`async: <seconds>`** = managed-node-side timeout (kill if exceeded).
- **`poll: 0`** = fire-and-forget, SSH connection closed immediately.
- **`poll: > 0`** = sync with heartbeat every N seconds (connection open but lightweight).
- **`async_status:` + `jid:`** = retrieval of the result (to be used with `until: finished`).
- **Several jobs in parallel on the same host** = **local parallelization** pattern.
- **`async:` must be > max duration** otherwise the job is killed prematurely.

## 🤔 Reflection questions

1. You want to launch a `dnf upgrade` that can take 30 min. You are behind
   a VPN that cuts idle sessions at 10 min. Which `async + poll` config
   do you use, and why not simply increase the SSH timeout?

2. A colleague puts `poll: 0` everywhere "to go faster". He does not capture the
   `jid` and does not do `async_status`. What is the concrete risk?

3. On 100 hosts, you want to launch a long download (5 min) in parallel. Why
   is `async + poll: 0` more efficient than `forks: 100` with a synchronous `command:`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`async: 0` + `poll: 0`**: **forbidden** combination (Ansible refuses). `async`
  must always have a value > 0.
- **The `async_wrapper` helper**: Ansible copies a Python script onto the managed
  node that supervises the task. If you kill the wrapper (`pkill async_wrapper`),
  you lose the `jid` (a real orphan job).
- **`mode: cleanup`** on `async_status:`: cleans up the temporary files on the
  managed node. To be used in a **maintenance** play if you accumulate
  status files in `~/.ansible_async/`.
- **`async + retries + delay` combination**: a **wait-for-condition** pattern
  much more efficient than `wait_for:` when the condition boils down to
  "this job finished cleanly".

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/async-poll/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/async-poll/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/async-poll/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
