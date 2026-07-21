# Lab 91 — Broken idempotence and performance tuning (forks, pipelining, ControlPersist)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Broken idempotence and performance tuning**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/)

An **idempotent** playbook shows `changed=0` on the **second run**. If you see `changed=N` on every run, **your tasks are lying** about their state: each run redoes everything, breaks HTTP/CDN caches, restarts services needlessly, and erodes trust in the code.

This lab teaches you to **diagnose** the 3 most frequent anti-patterns (`shell` without `creates:`, `lineinfile` without `regexp:`, `command` without `changed_when:`), to **fix** them, and to **measure** the impact of SSH optimizations (`pipelining`, `forks`, `ControlPersist`) on a playbook's total time.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Identify** the non-idempotent-by-default modules (`command`, `shell`, `raw`, `script`).
2. **Make** a `shell` **idempotent** with **`creates:`** or **`removes:`**.
3. **Force a task's `changed` verdict** with **`changed_when:`**.
4. **Measure** a time baseline with `profile_tasks` (see lab 89).
5. **Enable pipelining + forks=20 + ControlPersist=60s** in `ansible.cfg`.
6. **Compare** baseline vs optimized on a multi-host playbook.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible all -b -m ansible.builtin.file -a "path=/tmp/lab91-marker state=absent" 2>&1 | tail -2
```

## ⚙️ Target tree layout

```text
labs/troubleshooting/idempotence-perfs/
├── README.md
├── ansible.cfg                       ← (to create in exercise 5)
└── challenge/
    ├── README.md
    └── tests/
        └── test_idempotence.py
```

The learner writes `lab.yml` and `challenge/solution.yml` themselves.

## 📚 Exercise 1 — Anti-pattern: `shell` without `creates:`

```yaml
---
- hosts: db1.lab
  become: true
  tasks:
    - name: Créer un fichier marker (anti-pattern)
      ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
```

Run it **twice**:

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml | grep changed
```

Output:

```text
changed=1   ← run 1
changed=1   ← run 2 (PROBLEM: not idempotent)
```

🔍 **Observation**: `shell` **always** runs the command without checking state. **Always** `changed=1`.

### Fix with `creates:`

```yaml
- name: Créer un fichier marker (idempotent)
  ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
  args:
    creates: /tmp/lab91-marker        # ← skip if the file exists
```

Output after the fix:

```text
changed=1   ← run 1
changed=0   ← run 2 (correct)
```

## 📚 Exercise 2 — Anti-pattern: `lineinfile` without `regexp:`

```yaml
- name: Modifier la config (anti-pattern)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    line: "max_connections = 100"
    state: present
    create: true
```

Run it **twice**. If the value changes one day:

```yaml
- name: Modifier la config (anti-pattern, MAJ)
  ansible.builtin.lineinfile:
    line: "max_connections = 200"
```

The file now contains **both lines**: `max_connections = 100` AND `max_connections = 200`. **Duplication**.

### Fix with `regexp:`

```yaml
- name: Modifier la config (idempotent)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    regexp: '^max_connections\s*='   # ← matches existing lines
    line: "max_connections = 200"
    state: present
    create: true
```

🔍 **Observation**: with `regexp:`, lineinfile **replaces** the line instead of adding one. Always **set `regexp:`** unless you are sure of the first insertion.

## 📚 Exercise 3 — Anti-pattern: `command` without `changed_when:`

```yaml
- name: Vérifier la version curl
  ansible.builtin.command: curl --version
  # ↑ always returns changed=1 even though we only read
```

### Fix with `changed_when: false`

```yaml
- name: Vérifier la version curl
  ansible.builtin.command: curl --version
  changed_when: false                 # ← read-only, never a change
  register: curl_out
```

🔍 **Observation**: `changed_when: false` is the pattern for **read/diagnostic commands**. It preserves the playbook's idempotence.

## 📚 Exercise 4 — `changed_when:` conditional

A more subtle case: you want to signal `changed` **only** if the output contains an error.

```yaml
- name: Health check API
  ansible.builtin.uri:
    url: "http://localhost:8080/health"
    return_content: true
  register: health
  changed_when: "'OK' not in health.content"
```

🔍 **Observation**: `changed_when:` accepts a Jinja2/Python expression. It lets you **derive** the changed state from the task result, not from the module.

## 📚 Exercise 5 — Performance baseline

Create a playbook that runs **5 tasks** on **3 hosts**:

```yaml
---
- hosts: all
  gather_facts: true                 # ← intentionally expensive
  tasks:
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
```

Run it **without optimization** (default config):

```bash
time ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

Measure the time. On 3 hosts × 5 tasks × 0.5s + SSH overhead = ~15-20 s typical.

## 📚 Exercise 6 — Enable pipelining + forks + ControlPersist

Create `ansible.cfg` at the lab level:

```ini
[defaults]
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-fact-cache
fact_caching_timeout = 7200

[ssh_connection]
pipelining = True
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
```

Re-run:

```bash
time ANSIBLE_CONFIG=labs/troubleshooting/idempotence-perfs/ansible.cfg \
  ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

**Target: -50% to -60%** on the total time.

🔍 **Observation**: 3 combined levers:

- **`pipelining=True`**: removes `mkdir tmp + scp + exec` → 1 SSH instead of 3 per task.
- **`forks=20`**: runs 20 hosts in parallel (default 5).
- **`ControlPersist=60s`**: SSH connection **reused** for 60s. Avoids 1 handshake per task.

⚠️ **Pipelining incompatible with `requiretty`** in `/etc/sudoers`. On custom RHEL images, check.

## 📚 Exercise 7 — Test idempotence in CI

To automate the idempotence check in CI:

```bash
# Run 1
ansible-playbook lab.yml > /tmp/run1.log
# Run 2
ansible-playbook lab.yml | tee /tmp/run2.log

# Fail if the 2nd run has changes
grep -E 'changed=[1-9]' /tmp/run2.log && echo "IDEMPOTENCE KO" && exit 1
echo "IDEMPOTENCE OK"
```

🔍 **Observation**: an idempotence test in CI **blocks** regressions where a dev forgets a `changed_when:` or a `creates:`. **Put it in the `ansible-playbook --check --diff` pipeline**.

## 🔍 Observations to note

- **`command`, `shell`, `raw`, `script`** = non-idempotent by default.
- **`creates:`** / **`removes:`** make a `shell` idempotent via a file check.
- **`changed_when: false`** for read/diagnostic commands.
- **`lineinfile`** **always** with `regexp:`.
- **3 SSH levers**: `pipelining`, `forks`, `ControlPersist`.
- **Idempotence test** = run 2× and check `changed=0`.

## 🤔 Reflection questions

1. Why is `pipelining` disabled by default?
2. When is an explicit **`changed_when: true`** (instead of `false`) useful?
3. **`forks=200`** on a standard workstation: risks?
4. Does **`creates:` accept a glob** like `/tmp/lab91-*`? (Hint: no, exact path).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): refactor a **non-idempotent** playbook into an **idempotent** one with `creates:` + `regexp:` + `changed_when:`.

## 💡 Going further

- **Lab 92**: RHCE EX294 mock.
- **`ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks`** without touching
  `ansible.cfg`. A callback is enabled by name in that list; there is no
  `ANSIBLE_PROFILE_TASKS` variable, and setting it does nothing.
- **`stdout_callback = dense`**: 1 line per host (useful for 50+ host fleets).
- **`fact_caching = redis`** for fleets > 100 hosts (jsonfile becomes slow).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/troubleshooting/idempotence-perfs/lab.yml
ansible-lint --profile production labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```
