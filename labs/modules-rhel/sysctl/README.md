# Lab 46 — Module `sysctl:` (kernel parameters)

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

🔗 [**Ansible sysctl module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-sysctl/)

`ansible.posix.sysctl:` manages runtime **kernel parameters** via `sysctl`
(file `/etc/sysctl.conf` or `/etc/sysctl.d/*.conf`). Typical RHCE
2026 use cases: enable **IP forwarding**, tune the **network buffers**,
harden the security parameters (`kernel.kptr_restrict`,
`net.ipv4.tcp_syncookies`).

Module from the **`ansible.posix`** collection. Critical options: **`name:`**,
**`value:`**, **`state:`**, **`sysctl_file:`** (custom path in
`/etc/sysctl.d/`), **`reload:`** (applies now).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Modify** a kernel parameter with persistence and immediate application.
2. **Choose** between `/etc/sysctl.conf` (legacy) and `/etc/sysctl.d/<file>.conf`
   (modular).
3. **Distinguish** a **runtime** modification (sysctl -w) from a
   **persisted** one.
4. **Check** the current parameter via `command: sysctl -n` or
   `register: + reload:`.
5. **Diagnose** a parameter that reverts to its value after a reboot.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install ansible.posix
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /etc/sysctl.d/99-rhce-lab.conf; sysctl -p; true"
```

## 📚 Exercise 1 — Parameter in `/etc/sysctl.conf` (the default)

```yaml
---
- name: Demo sysctl
  hosts: db1.lab
  become: true
  tasks:
    - name: Activer l IP forwarding (persistant)
      ansible.posix.sysctl:
        name: net.ipv4.ip_forward
        value: '1'
        state: present
        reload: true

    - name: Verifier la valeur courante
      ansible.builtin.command: sysctl -n net.ipv4.ip_forward
      register: ip_fwd
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        msg: "ip_forward = {{ ip_fwd.stdout }}"
```

**Run it**:

```bash
ansible-playbook labs/modules-rhel/sysctl/lab.yml
```

🔍 **Observation**:

- The module modifies `/etc/sysctl.conf` (by default) or creates the line if absent.
- **`reload: true`** runs `sysctl -p` which applies the values immediately.
- 2nd run → `changed=0` (idempotent).

**Check persistence**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'grep net.ipv4.ip_forward /etc/sysctl.conf /etc/sysctl.d/* 2>/dev/null'
```

## 📚 Exercise 2 — `sysctl_file:` to modularize

Rather than piling everything into `/etc/sysctl.conf`, it is better to have **one file per
role** in `/etc/sysctl.d/`.

```yaml
- name: Tuning reseau dans /etc/sysctl.d/99-rhce-lab.conf
  ansible.posix.sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    state: present
    sysctl_file: /etc/sysctl.d/99-rhce-lab.conf
    reload: true
  loop:
    - { name: net.core.somaxconn, value: '4096' }
    - { name: net.ipv4.tcp_max_syn_backlog, value: '8192' }
    - { name: net.ipv4.tcp_syncookies, value: '1' }
```

🔍 **Observation**: a single file `/etc/sysctl.d/99-rhce-lab.conf` holds
the 3 parameters. **Advantages**:

- **Versioned** in the Ansible repo (`fetch:` for audit).
- **Cleanly removable**: `state: absent` removes the line.
- **Numeric prefix** (`99-`) controls the load order (see
  systemd-sysctl(8) doc: alphabetical order).

## 📚 Exercise 3 — The trap: `reload: false`

```yaml
- name: Modifier sans reload
  ansible.posix.sysctl:
    name: vm.swappiness
    value: '10'
    state: present
    reload: false   # Default: false!
```

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sysctl -n vm.swappiness'
# → 60 (the old value, not 10!)

ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /etc/sysctl.conf | grep swappiness'
# → vm.swappiness = 10 (modified persistently)
```

🔍 **Observation**: without `reload: true`, the parameter is modified in the
file **but not applied** to the runtime: it will need a manual `sysctl -p`
or a reboot to take effect.

**Rule**: **always** `reload: true` if you want the immediate effect.
Exception: if you have several consecutive `sysctl:`, set `reload:
false` everywhere EXCEPT on the last one (saving N-1 reloads).

## 📚 Exercise 4 — Removing a parameter

```yaml
- name: Retirer le tuning si plus necessaire
  ansible.posix.sysctl:
    name: net.core.somaxconn
    state: absent
    sysctl_file: /etc/sysctl.d/99-rhce-lab.conf
    reload: true
```

🔍 **Observation**: `state: absent` removes the line from the file. If the parameter
was overridden via several files (for example also in
`/etc/sysctl.conf`), the **second** one takes over: always audit after
removal.

**Check the effective value**:

```yaml
- ansible.builtin.command: sysctl -n net.core.somaxconn
  register: somaxconn
  changed_when: false

- ansible.builtin.debug:
    msg: "Valeur courante : {{ somaxconn.stdout }}"
    # → Will be the default kernel value (4096 on RHEL 10)
```

## 📚 Exercise 5 — CIS hardening pattern

The CIS Benchmark RHEL mandates about ten `sysctl` parameters for
hardening.

```yaml
- name: Durcissement CIS (sysctl)
  ansible.posix.sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    state: present
    sysctl_file: /etc/sysctl.d/99-cis-hardening.conf
    reload: true
  loop:
    # Network
    - { name: net.ipv4.conf.all.send_redirects, value: '0' }
    - { name: net.ipv4.conf.default.send_redirects, value: '0' }
    - { name: net.ipv4.conf.all.accept_redirects, value: '0' }
    - { name: net.ipv4.conf.all.accept_source_route, value: '0' }
    - { name: net.ipv4.tcp_syncookies, value: '1' }

    # Kernel security
    - { name: kernel.kptr_restrict, value: '2' }
    - { name: kernel.dmesg_restrict, value: '1' }
    - { name: kernel.randomize_va_space, value: '2' }

    # FS
    - { name: fs.suid_dumpable, value: '0' }
```

🔍 **Observation**: the **list of dicts** + `loop:` pattern keeps the code clean
and auditable (a dedicated file, grouped parameters, editable without touching the
playbook).

## 📚 Exercise 6 — The trap: parameters with `.` or `/`

Some parameters include **interface names**:

```yaml
# For eth0
- ansible.posix.sysctl:
    name: net.ipv4.conf.eth0.forwarding
    value: '1'
```

On RHEL 10, the interfaces are often named `enp0s3`, `ens18`, etc.: the
name must **match exactly** what `ip a` returns.

**Defensive pattern**:

```yaml
- name: Activer forwarding sur l interface principale
  ansible.posix.sysctl:
    name: "net.ipv4.conf.{{ ansible_default_ipv4.interface }}.forwarding"
    value: '1'
    state: present
    reload: true
```

`ansible_default_ipv4.interface` is the **fact** that gives the name of
the main interface: it works on any distro.

## 🔍 Observations to note

- **`ansible.posix.sysctl:`** = persisted kernel parameters.
- **`reload: true`** to apply immediately (otherwise it stays in the file).
- **`sysctl_file: /etc/sysctl.d/<name>.conf`** = preferred modular pattern.
- **`state: absent`** removes the line (but other files may take over).
- **Numeric prefix** in `sysctl.d/` controls the order (`99-` = applied last).
- **CIS pattern**: a dedicated file `/etc/sysctl.d/99-cis-hardening.conf`.

## 🤔 Reflection questions

1. You want to **cancel** a `sysctl` parameter set by the system (RHEL
   defaults). Is `state: absent` enough? Why can the parameter "come back"?

2. You have 10 parameters to modify in one pass. What is the **performance
   impact** of `reload: true` on each one vs `reload: true` on the last one
   only?

3. A `sysctl` parameter is modified in several places
   (`/etc/sysctl.conf`, `/etc/sysctl.d/99-app.conf`, `/etc/sysctl.d/99-cis.conf`).
   Which one **wins** at boot?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`reload_required:`**: on some parameters (`kernel.hostname`,
  `kernel.modules_disabled`), the `reload` is not enough: a reboot is needed.
  The module reports it in its output.
- **Module `community.general.modprobe:`**: load a kernel module
  (`ip_vs`, `nf_conntrack`), often a prerequisite for specific `sysctl`
  parameters.
- **`/run/sysctl.d/` vs `/etc/sysctl.d/`**: `/run/` is volatile (lost at
  reboot). For **transient** configs (containers).
- **`sysctl_set: true` pattern**: an option that **checks** that the parameter is
  really **readable** by sysctl before writing into the file. Safety
  against typos.
- **Lab 44 (firewalld)** + **45 (selinux)** + **46 (sysctl)** = the RHEL
  hardening trinity.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-rhel/sysctl/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-rhel/sysctl/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-rhel/sysctl/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
