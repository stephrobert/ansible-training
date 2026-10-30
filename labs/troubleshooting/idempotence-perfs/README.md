# Lab 91 - Broken idempotence and performance tuning (forks, pipelining, ControlPersist)

> **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## Recap

Companion guide: [**Broken idempotence and performance tuning**](https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/)

An **idempotent** playbook shows `changed=0` on the **second run**: it found the system already in the wanted state and touched nothing. When `changed=N` comes back on every run, the recap can no longer tell a real change from a task that replays for nothing, and a service may be restarted for no reason.

This lab has you diagnose the three most frequent causes (`shell` without `creates:`, `lineinfile` without `regexp:`, a read-only `command` without `changed_when:`), fix them, then measure the effect of connection settings (`pipelining`, `forks`, `ControlPersist`) on a playbook's total time.

## Objectives

By the end of this lab you will be able to:

1. Identify the modules that are not idempotent by default (`command`, `shell`, `raw`, `script`).
2. Make a `shell` idempotent with `creates:` or `removes:`.
3. Set a task's `changed` verdict with `changed_when:`, and tell it apart from `failed_when:`.
4. Take a baseline measurement with `profile_tasks` (see lab 89).
5. Tune `pipelining` and `forks` in `ansible.cfg`, and know that `ControlPersist=60s` is already active by default.
6. Compare the baseline and the tuned version on a multi-host playbook.

## Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible all -b -m ansible.builtin.file -a "path=/tmp/lab91-marker state=absent" 2>&1 | tail -2
```

## Target tree layout

You write `lab.yml` and `challenge/solution.yml` yourself, and you create `ansible.cfg` in exercise 6.

```text
labs/troubleshooting/idempotence-perfs/
├── README.md
├── ansible.cfg                       ← (to create in ex. 6)
└── challenge/
    ├── README.md
    └── tests/
        └── test_functional.py
```

## Exercise 1 - `shell` without `creates:`

The `shell` module runs its command on every execution, without looking at the target's state. The following playbook creates a marker file:

```yaml
---
- hosts: db1.lab
  become: true
  tasks:
    - name: Create a marker file (anti-pattern)
      ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
```

Run it **twice** and read the recap:

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml | grep changed
```

You get `changed=1` on both runs: the second should change nothing, so the task is not idempotent.

### Fix with `creates:`

The `creates:` argument tells Ansible to skip the command when the file already exists:

```yaml
- name: Create a marker file (idempotent)
  ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
  args:
    creates: /tmp/lab91-marker        # ← skipped if the file exists
```

After the fix, the first run shows `changed=1` and the second `changed=0`.

## Exercise 2 - `lineinfile` without `regexp:`

Without `regexp:`, `lineinfile` looks for the exact line given in `line:`. If the value changes later, it no longer recognises the old line and appends a second one.

```yaml
- name: Edit the config (anti-pattern)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    line: "max_connections = 100"
    state: present
    create: true
```

Run it twice, then change the value to `max_connections = 200`: the file now holds both lines, `max_connections = 100` and `max_connections = 200`.

### Fix with `regexp:`

With `regexp:`, the module finds the existing line and replaces it:

```yaml
- name: Edit the config (idempotent)
  ansible.builtin.lineinfile:
    path: /tmp/lab91-config.cfg
    regexp: '^max_connections\s*='   # ← recognises the existing line
    line: "max_connections = 200"
    state: present
    create: true
```

Set `regexp:` from the very first write of the directive: that is what lets you change it later without a duplicate.

## Exercise 3 - read-only `command` without `changed_when:`

A read-only command changes nothing, but `command` reports it as `changed` every time:

```yaml
- name: Check the curl version
  ansible.builtin.command: curl --version
  # without changed_when, this read is counted as a change
```

### Fix with `changed_when: false`

For a read, the answer is `false`:

```yaml
- name: Check the curl version
  ansible.builtin.command: curl --version
  changed_when: false                 # ← read-only, never a change
  register: curl_out
```

The task is `ok` on every run, and a real change elsewhere in the playbook stays visible in the recap.

## Exercise 4 - `changed_when:` with an expression, and `failed_when:`

Some commands act without telling Ansible, but their output says whether they did something. You then read that output to set the verdict. `git init` writes `Initialized empty Git repository` the first time, and `Reinitialized existing Git repository` when the repository already exists. In real life you would use the `git` or `file` module; the command only shows the mechanism here:

```yaml
- name: Initialise the repository
  ansible.builtin.command: git init /tmp/depot
  register: init
  changed_when: "'Reinitialized' not in init.stdout"
```

On the first run the task is `changed`, on the second it is `ok`, even though the command did run again.

`changed_when:` says nothing about whether the task succeeded. To decide that a result is a failure, you need `failed_when:`. A health check that gets a bad answer must not show up as "changed": it must fail the task, and since it modifies nothing, you declare that with `changed_when: false`.

```yaml
- name: Check the application health
  ansible.builtin.uri:
    url: "http://localhost:8080/health"
    return_content: true
  register: health
  changed_when: false
  failed_when: "'OK' not in health.content"
```

If the server answers 200 with `KO` in the body, the task fails and the recap shows `failed=1`, with no `changed`. With `OK` in the body, it is `ok`.

## Exercise 5 - Baseline measurement

Before tuning anything, measure. Create a playbook that runs five tasks on several hosts, with fact gathering on:

```yaml
---
- hosts: all
  gather_facts: true
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

Run it with the default configuration and note the time:

```bash
time ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

The time depends on your environment: your own value is the baseline, so record it.

## Exercise 6 - Tune pipelining and forks

Create an `ansible.cfg` at the lab level:

```ini
[defaults]
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-fact-cache
fact_caching_timeout = 7200

[ssh_connection]
pipelining = True
```

Re-run the same measurement:

```bash
time ANSIBLE_CONFIG=labs/troubleshooting/idempotence-perfs/ansible.cfg \
  ansible-playbook labs/troubleshooting/idempotence-perfs/lab.yml
```

Compare with your exercise 5 measurement: the difference is the real gain in your environment.

Three mechanisms are at work:

- `pipelining = True` avoids copying the module to the target before running it: execution goes through a single SSH connection instead of several per task.
- `forks = 20` runs up to 20 hosts in parallel (the default is 5).
- `ControlPersist` makes SSH reuse an open connection for the following tasks. It is already active: the default `ssh_args` is `-C -o ControlMaster=auto -o ControlPersist=60s` (`ansible-doc -t connection ansible.builtin.ssh`), so there is nothing to enable. An `ssh_args` line in `ansible.cfg` replaces that value **entirely**: if you set it to lengthen the duration (`ControlPersist=300s`), also keep `-C` and `ControlMaster=auto`, otherwise you lose connection reuse instead of improving it.

Pipelining is incompatible with `requiretty` in `/etc/sudoers`. On custom RHEL images, check that setting.

## Exercise 7 - Test idempotence in CI

The test plays the playbook twice on a disposable target and requires the second run to change nothing. Both runs must also succeed: a playbook that fails on the second run is not idempotent, even if no `changed` appears.

The trap in a naive script is `tee`. In a shell pipeline, the exit code is that of the last command, so that of `tee`, which always succeeds. Without `set -o pipefail`, a failing `ansible-playbook` goes unnoticed, and looking only for `changed=[1-9]` in the log detects nothing if the play stopped before changing anything.

```bash
#!/usr/bin/env bash
set -euo pipefail

playbook="${1:?usage: $0 playbook.yml}"
log="$(mktemp)"
export ANSIBLE_NOCOLOR=1

# First run: it may modify the target, but it must succeed.
ansible-playbook "$playbook"

# Second run: same success required, and no change.
ansible-playbook "$playbook" | tee "$log"

if grep -Eq '(changed|failed|unreachable)=[1-9]' "$log"; then
  echo "Idempotence KO: the second run changed or failed" >&2
  exit 1
fi
echo "Idempotence OK"
```

`set -e` stops the script if the first run fails. `pipefail` carries `ansible-playbook`'s exit code through the `tee`, so a failing second run also stops the script. The search in the recap (`PLAY RECAP`) covers the three counters that must stay at zero, and `ANSIBLE_NOCOLOR=1` keeps colour sequences out of the log.

This test is not the `--check --diff` mode. The latter simulates a run without changing anything and shows what would change: it detects drift on an existing system, or lets you review a change before applying it. It does not replace the idempotence test, because `command` and `shell` tasks are skipped in check mode (`skipping`), except with `creates:` or `removes:` (the condition is then evaluated without running the command, and the task reports `changed` if it would run), and because tasks that depend on their result cannot be evaluated. Idempotence can only be verified by really applying, hence the disposable target.

## Key points

- `command`, `shell`, `raw` and `script` are not idempotent by default.
- `creates:` and `removes:` make a `shell` idempotent through a file check.
- `changed_when: false` applies to read-only commands; `failed_when:` decides what counts as a failure.
- `lineinfile` is always written with `regexp:`.
- `ControlPersist=60s` is already the default; `pipelining` and `forks` are judged by a before/after measurement.
- An idempotence test requires both runs to succeed and the second to report no `changed`, `failed` or `unreachable`.

## Reflection questions

1. Why is `pipelining` disabled by default?
2. When is an explicit `changed_when: true` (instead of `false`) useful?
3. What are the risks of `forks=200` on a standard workstation?
4. Does `creates:` accept a glob like `/tmp/lab91-*`? (Hint: no, it is an exact path.)

## Final challenge

See [`challenge/README.md`](challenge/README.md): refactor a non-idempotent playbook into an idempotent one with `creates:`, `regexp:` and `changed_when:`.

## Going further

- Lab 92: RHCE EX294 mock.
- `ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks` enables timing
  without touching `ansible.cfg`. A callback is enabled by name in that list;
  there is no `ANSIBLE_PROFILE_TASKS` variable, and setting it does nothing.
- `stdout_callback = dense` prints one line per host (useful on large fleets).
- `fact_caching = redis` suits a large fleet better than `jsonfile`.

## Linting with `ansible-lint`

```bash
ansible-lint labs/troubleshooting/idempotence-perfs/lab.yml
ansible-lint --profile production labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```
