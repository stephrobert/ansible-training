# Lab 45 — Module `selinux:` and SELinux booleans

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

🔗 [**Ansible SELinux module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-selinux/)

SELinux (Security-Enhanced Linux) is the **mandatory access
control** system enabled by default on RHEL/AlmaLinux/Rocky in `enforcing` mode.
Three Ansible modules manage it:

- **`ansible.posix.selinux:`**: global state (enforcing / permissive / disabled)
  + active policy.
- **`ansible.posix.seboolean:`**: enable/disable SELinux **booleans**
  (`httpd_can_network_connect`, etc.).
- **`community.general.sefcontext:`**: manage file **contexts**
  (with `restorecon` to apply them).

These modules live in **`ansible.posix`** and **`community.general`**:
`ansible-galaxy collection install ansible.posix community.general`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Check** the SELinux state and mode (enforcing / permissive).
2. **Modify** a **SELinux boolean** with persistence.
3. **Define** a custom context on a directory (`sefcontext` + `restorecon`).
4. **Understand** why a reboot may be necessary (mode change).
5. **Diagnose** a service that crashes "because of SELinux".

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install ansible.posix community.general
ansible db1.lab -m ping

# Install the SELinux Python tools (needed by the modules)
ansible db1.lab -b -m dnf -a "name=python3-libselinux,policycoreutils-python-utils state=present"

ansible db1.lab -b -m shell -a "rm -rf /var/www/myapp; mkdir -p /var/www/myapp"
```

## 📚 Exercise 1 — Check the SELinux state

```yaml
---
- name: Demo selinux state
  hosts: db1.lab
  become: true
  tasks:
    - name: Verifier l etat SELinux courant
      ansible.builtin.command: getenforce
      register: enforce
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        msg: |
          Mode SELinux : {{ enforce.stdout }}
          ansible_selinux : {{ ansible_selinux.status | default('unknown') }}
          policy : {{ ansible_selinux.type | default('unknown') }}
```

🔍 **Observation**: `Enforcing` on AlmaLinux by default. The
`ansible_selinux.*` facts are collected automatically (`gather_facts: true`).

**3 possible modes**:

| Mode | Effect |
|---|---|
| `enforcing` | Constraints enforced + violations blocked (RHEL production) |
| `permissive` | Violations **logged** but **not blocked** (debug) |
| `disabled` | SELinux completely disabled (to avoid in prod) |

## 📚 Exercise 2 — Change the SELinux mode

```yaml
- name: Passer en permissive (debug temporaire)
  ansible.posix.selinux:
    policy: targeted
    state: permissive
```

🔍 **Observation**: the module modifies `/etc/selinux/config` (effect **after
reboot**) AND applies the mode **now** (`setenforce 0`).

**Disable completely** (to avoid except in special cases):

```yaml
- ansible.posix.selinux:
    state: disabled
  notify: Reboot system
```

`state: disabled` **requires a reboot** to take effect (the kernel must
reload the policy). The module modifies `/etc/selinux/config` but
**`getenforce`** will keep showing `Enforcing` until the reboot.

## 📚 Exercise 3 — SELinux booleans

SELinux **booleans** are switches that enable/disable rules
of the policy. E.g.: allow the web server to connect to the network.

> 💡 The web booleans are prefixed `httpd_` by historical legacy, but they
> do not target the Apache package: they target the **SELinux domain `httpd_t`**,
> the one of all web servers in the targeted policy. nginx runs in it too
> (`ps -eZ | grep nginx` shows `system_u:system_r:httpd_t:s0`), so everything
> that follows applies to the training, which deploys nginx.

```yaml
- name: Lister les booleens HTTPD
  ansible.builtin.command: getsebool -a
  register: bools
  changed_when: false

- name: Filtrer ceux contenant "httpd"
  ansible.builtin.debug:
    msg: "{{ bools.stdout_lines | select('search', 'httpd') | list | first(5) }}"
```

🔍 **Observation**: on RHEL 10, there are ~300 booleans. The most useful for RHCE:

| Boolean | Effect |
|---|---|
| `httpd_can_network_connect` | the web server can make outbound connections |
| `httpd_can_network_connect_db` | the web server can connect to a remote DB |
| `httpd_enable_homedirs` | the web server can serve `~user/public_html/` |
| `nfs_export_all_rw` | NFS export in read-write |
| `samba_enable_home_dirs` | Samba can share the homes |

## 📚 Exercise 4 — Modify a boolean with persistence

```yaml
- name: Autoriser le serveur web a se connecter au reseau (persistant)
  ansible.posix.seboolean:
    name: httpd_can_network_connect
    state: true
    persistent: true
```

🔍 **Observation**:

- **Without `persistent: true`**: change only at **runtime** (lost at
  reboot, equivalent to a plain `setsebool`).
- **With `persistent: true`**: change **persisted** into the policy
  (equivalent to `setsebool -P`).

**For production**: **always** `persistent: true`. Without it, after a reboot
the service crashes again with the same SELinux errors.

## 📚 Exercise 5 — File contexts (`sefcontext`)

Frequent pattern: deploy a web app in a custom directory (not the default
web root, `/usr/share/nginx/html/` on RHEL). SELinux forbids the web
server to serve files that do not have the right **SELinux context**.

```yaml
- name: Definir le contexte httpd_sys_content_t pour /var/www/myapp
  community.general.sefcontext:
    target: '/var/www/myapp(/.*)?'
    setype: httpd_sys_content_t
    state: present

- name: Appliquer le contexte (restorecon)
  ansible.builtin.command: restorecon -Rv /var/www/myapp
  register: restorecon_result
  changed_when: "'relabeled' in restorecon_result.stdout"
```

🔍 **Observation**:

- **`sefcontext:`** adds the rule into the policy (`semanage fcontext -a -t
  httpd_sys_content_t '/var/www/myapp(/.*)?'`).
- **`restorecon -R`** applies the rule to the existing files (otherwise they
  keep their old context).

**Regex convention**: `(/.*)?` at the end to match the directory AND all its
sub-elements.

## 📚 Exercise 6 — Diagnose a SELinux violation

```yaml
- name: Tenter d acceder a /var/www/myapp via le serveur web
  ansible.builtin.uri:
    url: http://localhost/myapp/
    status_code: [200, 403]   # We accept 403 if SELinux blocks

- name: Verifier les violations dans audit.log
  ansible.builtin.command: |
    grep "denied" /var/log/audit/audit.log | tail -5
  register: denials
  changed_when: false
  failed_when: false
```

🔍 **Observation**: if SELinux blocks, `audit.log` contains entries
`type=AVC msg=audit ... denied`. The **`audit2allow`** tool (package
`policycoreutils-python-utils`) generates a SELinux module that allows
exactly what is blocked:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo audit2allow -a -M myapp_local'
sudo semodule -i myapp_local.pp
```

**But**: **never** run `audit2allow -a -M` blindly in prod, it is
often a bad idea. Prefer fixing the context (`sefcontext`) or
enabling a boolean.

## 📚 Exercise 7 — The trap: SELinux disabled during development

Dangerous pattern seen in prod:

```yaml
# ❌ Bad practice: disables SELinux "to make it work"
- ansible.posix.selinux:
    state: disabled
```

🔍 **Risks**:

- **Increased attack surface**: SELinux is a critical layer of defense
  against exploits.
- **Failed audit**: RHCE EX294, CIS Benchmark, ANSSI require SELinux enabled.
- **Dev/prod drift**: the code works in dev (SELinux off) but crashes in prod
  (SELinux on).

**Good practice**: switch to `permissive` to debug → identify the
missing contexts/booleans → fix → go back to `enforcing`.

## 🔍 Observations to note

- **`ansible.posix.selinux:`** = global state (`enforcing`/`permissive`/`disabled`).
- **`ansible.posix.seboolean:`** = booleans, **always `persistent: true`** in prod.
- **`community.general.sefcontext:`** + **`restorecon -R`** = file contexts.
- **A change to `disabled`** requires a **reboot** to take effect.
- **`policycoreutils-python-utils`** must be installed on the managed node.
- **Never disable SELinux** except in a documented critical case.

## 🤔 Reflection questions

1. You deploy an app in `/opt/myapp/` that must be served by nginx.
   nginx cannot access it. Which pipeline (boolean, sefcontext,
   restorecon)?

2. Why is `state: permissive` **more useful** than `state: disabled`
   for **debugging**? (hint: violations still logged).

3. You want to **list all the contexts** defined on a directory. Which
   shell command + which Ansible module?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`community.general.seport:`**: associate a **port** with a SELinux type.
  The `httpd_t` domain is only allowed to bind to two types: `http_port_t`
  (80, 81, 443, 488, 8008, 8009, 8443, 9000) and `http_cache_port_t` (8080,
  8118, 8123, 10001-10010). Any other port must be labeled, otherwise the bind
  fails with "Permission denied". Beware the trap: **8080 already works
  out of the box** (it is in `http_cache_port_t`), so it is not a good
  example. The `premiers-pas/premier-playbook` lab uses 8888, which really is
  denied by default. Check your machine's policy:
  `semanage port -l | grep -E '^http_(port|cache_port)_t'`.
- **`audit2allow -a`**: generate a **custom SELinux module** from the
  logged violations. A **troubleshooting** tool, not for blind production.
- **Multi-policy**: RHEL 10 supports `targeted` (default) and `mls`
  (Multi-Level Security, defense sector). Not in RHCE.
- **`semanage` CLI**: the reference command to explore the policy
  (`semanage fcontext -l`, `semanage port -l`, `semanage boolean -l`).
- **Lab 44 (firewalld)**: complement SELinux with network rules for
  defense-in-depth security.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-rhel/selinux/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-rhel/selinux/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-rhel/selinux/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
