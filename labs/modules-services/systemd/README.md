# Lab 38 — `systemd_service:` module (manage systemd services)

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

🔗 [**Ansible systemd_service module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-systemd/)

On modern distributions (RHEL 7+, Ubuntu 16.04+), **all services**
are managed by **systemd**. The `ansible.builtin.systemd_service:` module
(alias `systemd`) is more powerful than the legacy `service:`:

- **Knows `daemon_reload:`** (reload systemd after modifying a `.service`).
- **Distinguishes `state:`** (immediate state) and **`enabled:`** (at boot): two
  independent options.
- **Handles masked unit files** (`masked: true`).
- **Can reload without restarting** (`state: reloaded`).

It is the number-one module for service operations in RHCE 2026.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Distinguish** `state:` vs `enabled:` (current state vs boot).
2. **Reload** a service without downtime (`reloaded` vs `restarted`).
3. **Drop a custom unit file** + `daemon_reload: true`.
4. **Mask** a dangerous service (`masked: true`).
5. **Notify** a service from a handler (reload-on-change pattern).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "rm -f /etc/systemd/system/lab-marker.service /var/run/lab-marker.flag; systemctl daemon-reload"
```

## 📚 Exercise 1 — `state:` vs `enabled:` (two independent options)

Create `lab.yml`:

```yaml
---
- name: Demo systemd state vs enabled
  hosts: web1.lab
  become: true
  tasks:
    - name: Installer chrony
      ansible.builtin.dnf:
        name: chrony
        state: present

    - name: Demarrer MAINTENANT (mais pas au boot)
      ansible.builtin.systemd_service:
        name: chronyd
        state: started

    - name: Verifier le statut
      ansible.builtin.command: systemctl is-active chronyd
      register: chronyd_active
      changed_when: false

    - name: Verifier si enabled au boot
      ansible.builtin.command: systemctl is-enabled chronyd
      register: chronyd_enabled
      changed_when: false
      failed_when: false

    - name: Resume
      ansible.builtin.debug:
        msg: |
          active : {{ chronyd_active.stdout }}
          enabled : {{ chronyd_enabled.stdout }}
```

**Run**:

```bash
ansible-playbook labs/modules-services/systemd/lab.yml
```

🔍 **Observation**: the service is **active** (running now) but can be
**disabled** (not at boot) depending on the initial state. **`state:`** and **`enabled:`**
are **independent**.

**Normal configuration**: both together.

```yaml
- ansible.builtin.systemd_service:
    name: chronyd
    state: started
    enabled: true
```

## 📚 Exercise 2 — `reloaded` vs `restarted`

```yaml
- name: Modifier la conf chrony
  ansible.builtin.lineinfile:
    path: /etc/chrony.conf
    regexp: '^server '
    line: 'server 0.fr.pool.ntp.org iburst'

- name: Recharger SANS coupure
  ansible.builtin.systemd_service:
    name: chronyd
    state: reloaded

# Alternative: restarted (with downtime)
- name: Redemarrer (coupure breve)
  ansible.builtin.systemd_service:
    name: chronyd
    state: restarted
```

| `state:` | Effect | Downtime |
|---|---|---|
| `restarted` | `systemctl restart` (stop + start) | Yes, brief (ms to seconds) |
| `reloaded` | `systemctl reload` (SIGHUP, reloads config) | No, no stop |

🔍 **Observation**: prefer **`reloaded`** when the service supports it (`nginx`,
`sshd`, `firewalld`, `chronyd`): no downtime for connected clients.

**`restarted`** stays necessary for:

- A change of **unit file** (the binary or the arguments change).
- A major change that SIGHUP does not cover.

## 📚 Exercise 3 — `daemon_reload:` after a new unit file

```yaml
- name: Deposer un unit file custom
  ansible.builtin.copy:
    content: |
      [Unit]
      Description=Lab Marker Service
      After=network.target

      [Service]
      Type=oneshot
      ExecStart=/bin/touch /var/run/lab-marker.flag
      RemainAfterExit=yes

      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/lab-marker.service
    mode: "0644"

- name: Recharger systemd ET activer le service
  ansible.builtin.systemd_service:
    name: lab-marker
    state: started
    enabled: true
    daemon_reload: true
```

🔍 **Observation**:

- **Without `daemon_reload: true`**, systemd **does not see** the new unit file →
  `start` would fail with "unit not found".
- **With `daemon_reload: true`**, systemd reloads its unit files **before**
  acting on the service.

**When to use it**: **only** when you **drop or modify** a unit
file. No need on a `state: started` of a standard system service.

**Check that it works**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'systemctl status lab-marker && cat /var/run/lab-marker.flag'
```

## 📚 Exercise 4 — `masked: true` (forbid the start)

```yaml
- name: Masquer rpcbind (durcissement)
  ansible.builtin.systemd_service:
    name: rpcbind
    state: stopped
    enabled: false
    masked: true
```

🔍 **Observation**: **`masked: true`** links the unit file to `/dev/null`: any
`systemctl start rpcbind` command fails silently, **even by a human**.
Absolute **hardening** pattern for services you **forbid**.

**Difference with `enabled: false`**:

- **`disabled`** = not at boot, but a manual `systemctl start` works.
- **`masked`** = forbids any form of start.

**To unmask**:

```yaml
- ansible.builtin.systemd_service:
    name: rpcbind
    masked: false
    state: started
```

## 📚 Exercise 5 — Handler pattern (notification)

```yaml
- name: Modifier sshd_config
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'
  notify: Reload sshd

# Further down in the play (handlers section)
handlers:
  - name: Reload sshd
    ansible.builtin.systemd_service:
      name: sshd
      state: reloaded
```

🔍 **Observation**: the `Reload sshd` handler only runs **if the
`lineinfile:` task notified** (= effective change), and **at the end of the play**.

**Advantages**:

- No useless reload if nothing changed.
- Reload at **end of play**: if several tasks notify the same handler,
  it runs **only once**.

See [Lab 06 - Handlers](../../ecrire-code/handlers/) for the details.

## 📚 Exercise 6 — Loop over several services

```yaml
- name: Demarrer la stack monitoring
  ansible.builtin.systemd_service:
    name: "{{ item }}"
    state: started
    enabled: true
  loop:
    - chronyd
    - sshd
    - rsyslog
```

🔍 **Observation**: each iteration is **an independent systemd operation**.
For 50 services it is slow, but it is rare to have 50 services to start
in parallel.

**No benefit to writing `state: [...]`**: `name:` accepts only one service.

## 📚 Exercise 7 — The trap: missing `[Install]`

If your custom unit file has **no `[Install]` section**, `enabled: true`
**fails silently**: the service will not be started at boot.

```ini
# ❌ Bad: no [Install]
[Unit]
Description=Mon service

[Service]
ExecStart=/usr/local/bin/myapp

# ✅ Good: [Install] with WantedBy
[Unit]
Description=Mon service

[Service]
ExecStart=/usr/local/bin/myapp

[Install]
WantedBy=multi-user.target
```

🔍 **Observation**: without `[Install]`, `systemctl enable` returns `Created
symlink ... → ...` but **nothing is created in `/etc/systemd/system/multi-user.target.wants/`**.
At reboot, the service does not start.

**Always** check that a custom unit file has `[Install] WantedBy=...`.

## 🔍 Observations to note

- **`state:`** = **immediate** state (started/stopped/restarted/reloaded).
- **`enabled:`** = start **at boot** (independent of `state:`).
- **`reloaded`** > **`restarted`** when the service supports it: no downtime.
- **`daemon_reload: true`** is mandatory **after** a new unit file.
- **`masked: true`** = hardening (forbids any start, even manual).
- **The `[Install]` section** in the unit file is mandatory for `enabled: true`.

## 🤔 Reflection questions

1. You modify `nginx.conf` via `template:`. Which option of the
   `systemd_service:` module (with `notify:` from the `template:`) guarantees zero downtime for
   the clients?

2. What is the difference between `disabled` and `masked` from the
   **human operator** point of view on a server? (hint: can an operator still
   `systemctl start`?)

3. You want to create 5 custom services from a single unit-file template.
   Which pattern (combining `template`, `loop:`, `daemon_reload:`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`force: true`**: forces the action even if it seems idempotent. Useful for
  a `restarted` after external detection of a degraded state.
- **`service:` module (legacy)**: pre-systemd alternative, still available.
  Useful only on distros without systemd (very rare today).
- **`scope: user`**: manage **user** services (`systemctl --user`).
  Advanced, rarely used in RHCE.
- **`socket activation` pattern**: drop a `.socket` + `.service` to
  start the service on demand (not permanently).
- **Lab 39 (`cron:`)**: for **scheduled tasks** rather than long-living
  services.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-services/systemd/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-services/systemd/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-services/systemd/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
