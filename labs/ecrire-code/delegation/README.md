# Lab 11 — Delegation (`delegate_to`, `run_once`, `local_action`)

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

🔗 [**Ansible delegation: delegate_to, run_once, local_action**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/delegation/)

`delegate_to:` redirects the execution of a task to **another host** than the one targeted
by the play. `run_once: true` runs the task **only once** (on the first host
of the batch, or on the delegated host). `local_action:` is a shortcut for
`delegate_to: localhost`. These 3 tools are the **basis of multi-host patterns**:
notifying an external load balancer, creating a DNS record, putting a machine into
maintenance, triggering a centralized backup.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Redirect** a task to another managed node via `delegate_to:`.
2. **Run** a task **only once** in a multi-host play (`run_once`).
3. **Combine** `delegate_to + run_once` for notification patterns.
4. **Use** `local_action:` for control-node-side operations.
5. **Distinguish** `delegate_facts: true` from a plain `delegate_to:`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible webservers -m ping
ansible db1.lab -m ping
# All must be SUCCESS
```

Clean up the markers from previous runs:

```bash
ansible all -b -m file -a "path=/tmp/delegated-from-webservers.txt state=absent"
ansible all -b -m file -a "path=/tmp/local-action-marker.txt state=absent"
```

## 📚 Exercise 1 — Plain `delegate_to:` (without `run_once`)

Create `lab.yml`:

```yaml
---
- name: Demo delegate_to (sans run_once)
  hosts: webservers
  become: true
  tasks:
    - name: Annoncer chaque webserver sur db1
      ansible.builtin.copy:
        dest: "/tmp/announce-{{ inventory_hostname }}.txt"
        content: "Webserver {{ inventory_hostname }} ({{ ansible_default_ipv4.address }}) en service\n"
        mode: "0644"
      delegate_to: db1.lab
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/delegation/lab.yml
```

🔍 **Observation**: the task runs **on db1.lab** (not on web1/web2), but **twice**
(once per webserver), creating 2 files `/tmp/announce-web1.lab.txt` and
`/tmp/announce-web2.lab.txt` on db1.

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'ls /tmp/announce-*.txt'
```

**Variables**: `inventory_hostname` stays that of the **loop** (web1, then web2), not
db1. This is the subtlety: the task **runs** on db1 but sees the vars of the
current play host.

## 📚 Exercise 2 — `delegate_to + run_once`

Modify `lab.yml`:

```yaml
---
- name: Demo delegate_to + run_once
  hosts: webservers
  become: true
  tasks:
    - name: Notifier la DB une seule fois
      ansible.builtin.copy:
        dest: /tmp/delegated-from-webservers.txt
        content: "Deploy webservers OK, declenche par {{ inventory_hostname }} a {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"
      delegate_to: db1.lab
      run_once: true
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/delegation/lab.yml
```

🔍 **Observation**: a **single** file `/tmp/delegated-from-webservers.txt` on db1,
containing the **first webserver** of the play (web1.lab in alphabetical order). This is
the **"end of deployment" notification** pattern: you notify db1 once the ENTIRE web
fleet has been deployed, not once per webserver.

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /tmp/delegated-from-webservers.txt'
```

## 📚 Exercise 3 — `local_action:` (shortcut for the control node)

To run a task **on the control node** (your machine), `local_action:` is
shorter than `delegate_to: localhost`.

```yaml
---
- name: Log local apres deploy
  hosts: webservers
  tasks:
    - name: Marquer le deploy dans un log local
      local_action:
        module: ansible.builtin.copy
        content: "Deploy {{ inventory_hostname }} OK a {{ ansible_date_time.iso8601 }}\n"
        dest: "/tmp/local-action-marker-{{ inventory_hostname }}.txt"
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/delegation/lab-localaction.yml
ls /tmp/local-action-marker-*.txt
```

🔍 **Observation**: 2 files are created **on your local machine** (not on web1/web2).
`local_action:` is strictly equivalent to `delegate_to: localhost` but is written in
fewer lines.

**Note**: no automatic `become:` with `local_action:`. To write into `/etc/`
on the local side, you still need `become: true`.

## 📚 Exercise 4 — `delegate_facts: true` (capturing another host's facts)

Use case: your play runs on the `webservers`, but you need to **read
db1's facts** (to get its IP, its OS version, etc.).

```yaml
---
- name: Pre-collecter les facts de db1
  hosts: webservers
  tasks:
    - name: Gather facts de db1.lab
      ansible.builtin.setup:
      delegate_to: db1.lab
      delegate_facts: true
      run_once: true

    - name: Utiliser ces facts cote webserver
      ansible.builtin.debug:
        msg: |
          Webserver {{ inventory_hostname }} pourra parler a db1
          IP db1 : {{ hostvars['db1.lab'].ansible_default_ipv4.address }}
          OS db1 : {{ hostvars['db1.lab'].ansible_distribution }}
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/delegation/lab-delegate-facts.yml
```

🔍 **Observation**:

- **Without `delegate_facts: true`**, the collected facts would go into
  `hostvars['web1.lab'].ansible_*` (wrong!) because the play runs on web1.
- **With `delegate_facts: true`**, the facts go into `hostvars['db1.lab'].ansible_*`
  (correct).

**Without this option**, you have the classic trap: the facts are stored under the
wrong hostname and you reference the wrong machine everywhere.

## 📚 Exercise 5 — The classic trap: `run_once` + `serial:`

`run_once: true` runs **only once per batch** when `serial:` is set.
If `serial: 1`, you have `N` batches → `run_once` runs **N times** in total!

Create `lab-piege.yml`:

```yaml
---
- name: Demo piege run_once + serial
  hosts: webservers
  become: true
  serial: 1
  tasks:
    - name: Cense ne tourner qu une fois (piege !)
      ansible.builtin.shell: |
        echo "Iteration a {{ ansible_date_time.iso8601 }}" >> /tmp/run-once-trap.txt
      delegate_to: db1.lab
      run_once: true
```

**Run and inspect**:

```bash
ansible-playbook labs/ecrire-code/delegation/lab-piege.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /tmp/run-once-trap.txt'
```

🔍 **Observation**: the file contains **2 lines** (one per batch web1, then web2),
**not 1** as expected. `run_once` is local to the batch, not global to the play.

**Solution**: if you really want **only once for the whole play**, do
the `delegate_to + run_once` in a **separate play** without `serial:`, or condition it
with `when: inventory_hostname == ansible_play_hosts_all[0]`.

## 🔍 Observations to note

- **`delegate_to: <host>`** = the task **runs** on this host, but **sees** the vars of the play host.
- **`run_once: true`** = the task runs **only once per batch** (not per play).
- **`local_action:`** = shortcut for `delegate_to: localhost`.
- **`delegate_facts: true`** = the collected facts are stored under the delegated host (not the play host).
- **Combination `delegate_to + run_once`** = notification pattern (load balancer, DNS, monitoring).

## 🤔 Reflection questions

1. You deploy to 50 webservers. Before restarting each webserver, you want
   to **remove it from the load balancer** (HAProxy on lb1.lab). How do you articulate
   `delegate_to`, `serial: 1`, and the pre/post tasks pattern?

2. `delegate_to: db1.lab` on a `command:` task that creates `/etc/myapp.conf`: what
   is the classic **variable trap**? (hint: is `inventory_hostname` db1's or the
   current play host's?)

3. Why can `run_once: true` without `delegate_to:` be surprising in a multi-host
   play? (On which host does the task run?)

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Blue/green pattern**: `delegate_to: load-balancer.lab` + `run_once: true` to
  switch traffic to the new release.
- **Dynamic DNS pattern**: create a DNS record via `delegate_to: dns.lab` and
  the Bind/PowerDNS API.
- **`delegate_to: 127.0.0.1`** vs **`delegate_to: localhost`**: subtle difference:
  `127.0.0.1` forces a local SSH connection, `localhost` uses the **local connection
  plugin** (no SSH). Prefer `localhost` (faster).
- **`add_host:` + `delegate_to:`**: dynamic inventory pattern. Create a host
  on the fly then delegate a task to it.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/delegation/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/delegation/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/delegation/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
