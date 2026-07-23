# Lab 54 — `wait_for:` and `pause:` modules (synchronization)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.

## 🧠 Recap

🔗 [**Ansible wait_for and pause modules**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-wait-for-pause/)

Two modules for **time synchronization** within a play:

- **`ansible.builtin.wait_for:`** = wait for **a condition** (open port, file
  created, regex in a file, SSH-ready machine). Active polling.
- **`ansible.builtin.pause:`** = wait for **a fixed delay** (seconds/minutes) or
  ask the operator for an **interactive confirmation**.

`wait_for:` is the **right choice** in 90% of cases: active polling until the
condition is true. `pause:` is useful for **incompressible delays** or **human
confirmations**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Wait for a TCP port to open** (the most common case).
2. **Wait for a port to close** (`state: stopped`).
3. **Wait for a file to appear** or for a **regex** in a file.
4. **Pause** simply (`seconds:`) or interactively (`prompt:`).
5. **Diagnose** a `wait_for:` timeout (wrong host, firewalled port).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/lab-waitfor-*"
```

## 📚 Exercise 1 — `wait_for: port:` (the most common)

Pattern number 1: after starting a service, wait for the port to be ready
before the tasks that depend on it.

```yaml
---
- name: Demo wait_for port
  hosts: db1.lab
  become: true
  tasks:
    - name: Demarrer chronyd (s il ne tourne pas)
      ansible.builtin.systemd_service:
        name: chronyd
        state: started

    - name: Attendre que le port chronyd 323 soit pret
      ansible.builtin.wait_for:
        port: 323
        host: 127.0.0.1
        timeout: 10
```

🔍 **Observation**: `wait_for:` polls (by default every second) until the port
is open, or fails after `timeout:` seconds.

**`host:`** default = `127.0.0.1`. To test a port on another host from the
managed node, specify `host: 10.10.20.21`.

## 📚 Exercise 2 — `state: stopped` (wait for the close)

```yaml
- name: Verifier que le port 9999 est BIEN libre
  ansible.builtin.wait_for:
    port: 9999
    host: 127.0.0.1
    state: stopped
    timeout: 5
```

🔍 **Observation**: `state: stopped` = **success if the port is free**. Handy
before starting a service, to check that nothing else is using the port.

**Failure case**: if the port is busy after `timeout`, the task is **failed**.
Lets you stop the play before a conflict.

## 📚 Exercise 3 — `wait_for: path:` (a file appears)

```yaml
- name: Lancer une commande qui crée un fichier (en arriere-plan)
  ansible.builtin.shell: |
    ( sleep 3 && touch /tmp/lab-waitfor-marker.txt ) &
    echo "lance en arriere-plan"
  changed_when: false

- name: Attendre que le fichier apparaisse
  ansible.builtin.wait_for:
    path: /tmp/lab-waitfor-marker.txt
    timeout: 10
```

🔍 **Observation**: `wait_for: path:` polls until the file **exists**. Useful to
synchronize with an asynchronous process that creates a flag-file at the end of
processing.

## 📚 Exercise 4 — `wait_for: search_regex:` (search for a regex)

```yaml
- name: Verifier qu un service a logge "Ready" dans son journal
  ansible.builtin.wait_for:
    path: /var/log/messages
    search_regex: 'systemd.*Started.*chronyd'
    timeout: 30
```

🔍 **Observation**: `wait_for:` reads the file and tests the regex at each poll.
Appears in the content → success. Timeout → failed.

**Use case**: wait for the "Server ready" log of an app, "Database initialized",
etc.

**Limitation**: `wait_for: search_regex:` reads the file **at each poll**: on a
log of several GB, it is slow. For very large logs, prefer `tail -F` + grep or a
dedicated module.

## 📚 Exercise 5 — Simple `pause:` (fixed delay)

```yaml
- name: Demarrer le service
  ansible.builtin.systemd_service:
    name: chronyd
    state: restarted

- name: Pause de 5 secondes pour stabilisation
  ansible.builtin.pause:
    seconds: 5

- name: Verifier la suite
  ansible.builtin.command: chronyc tracking
  register: chrony_status
  changed_when: false
```

🔍 **Observation**: **`pause: seconds:`** = sleep at the start of the play.
Simple but **not adaptive** (5s even if the service is ready in 1s). Prefer
`wait_for:` when a precise condition exists.

**When to prefer `pause:` over `wait_for:`**:

- No precise measurable condition.
- Delay imposed by an external system (API cool-down).
- Testing configurations that must take effect within a fixed time.

## 📚 Exercise 6 — `pause: prompt:` (interactive confirmation)

```yaml
- name: Confirmation manuelle avant migration BDD
  ansible.builtin.pause:
    prompt: |
      Vous allez lancer la migration de la base de production.
      Tapez ENTER pour continuer, Ctrl+C pour annuler.
```

🔍 **Observation**: Ansible **blocks** the play while waiting for a key. Use
case: critical operations where a human must validate.

**CI/CD pattern**: add `pause: + when: confirm_required | bool` to have the
confirmation **only in interactive mode**.

```yaml
- ansible.builtin.pause:
    prompt: "Confirmer la migration ? "
  when: confirm_required | default(false) | bool
```

In CI: `--extra-vars "confirm_required=false"` skips the pause.
In manual mode: it asks for confirmation.

## 📚 Exercise 7 — The trap: `wait_for:` that crashes at startup

Ansible can **start** a service via `systemd_service:` and **immediately move**
to `wait_for: port:`, without waiting for systemd to have actually started the
binary.

```yaml
# ❌ Race condition possible
- ansible.builtin.systemd_service:
    name: myapp
    state: started

- ansible.builtin.wait_for:
    port: 8080
    timeout: 30
  # Si myapp met 35s a demarrer → wait_for failed
```

🔍 **Observation**: the **race** happens if the VM is slow or if the app takes
time to initialize its sockets. Ansible **cannot** distinguish "systemd agreed
to start" from "the service is listening".

**Mitigation**:

- **Increase `timeout:`**: if the app can take 60s, set `timeout: 90`.
- **A minimum `pause:`** before the `wait_for:`: give the service at least a few
  seconds to start its network.
- **Combine with `until:` on `uri:`**: test an HTTP endpoint rather than a raw
  TCP port (lab 50).

## 📚 Exercise 8 — `delay:` for more spaced-out polling

```yaml
- name: Attendre un service lent (poll moins frequent)
  ansible.builtin.wait_for:
    port: 8080
    timeout: 300
    delay: 10        # Wait 10s before the 1st poll
    sleep: 5         # 5s between each poll
```

🔍 **Observation**: by default, `wait_for:` polls **every second** from the
start. On a very slow service (Docker registry, database), that is too much.
**`delay:`** delays the 1st poll. **`sleep:`** spaces out the subsequent polls.

## 🔍 Observations to note

- **`wait_for:`** = active polling until the condition is true.
- **`port:`** + `state: started/stopped` = the most common port test.
- **`path:`** = wait for a file to appear.
- **`search_regex:`** = search for a string in a file (slow on large logs).
- **`pause: seconds:`** = simple sleep, **not adaptive**.
- **`pause: prompt:`** = interactive human confirmation.
- **`timeout:`** on `wait_for:` = to be sized with margin (× 2 or × 3 of the
  expected time).

## 🤔 Reflection questions

1. You start `nginx`, which can take 2s to 30s depending on load. Which
   `systemd + wait_for` combination (with which parameters) guarantees the least
   risk without too much waiting?

2. Difference between `wait_for: port:` (raw TCP test) and `uri: until:` (HTTP
   test with status code)? When to prefer each?

3. You want to **block the play** between 2 `serial: 1` batches to manually
   check the 1st host before touching the 2nd. Which pattern?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`active_connection_states:`**: list the accepted TCP states (`ESTABLISHED`,
  `LISTEN`, `SYN_SENT`, etc.). Advanced.
- **`exclude_hosts:`**: `wait_for:` distributed over several hosts, exclude some.
- **`community.general.timeout` module**: decorator to limit an arbitrary task
  in time.
- **`uri: + until:`** (lab 50): alternative to `wait_for: port:` that also tests
  the **application** (HTTP 200 + body OK), not just the TCP port.
- **Lab 50 (`uri:`)** + **Lab 53 (`assert:`)**: the `wait_for + uri + assert`
  combination for robust healthchecks.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-diagnostic/wait-for-pause/lab.yml
ansible-lint labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
ansible-lint --profile production labs/modules-diagnostic/wait-for-pause/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
