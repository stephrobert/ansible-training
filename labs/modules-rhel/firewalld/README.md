# Lab 44 — Module `firewalld:` (manage the RHEL firewall)

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

🔗 [**Ansible firewalld module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-firewalld/)

`ansible.posix.firewalld:` manages **firewalld**, the default firewall on RHEL 7+,
AlmaLinux, RockyLinux. It is the #1 RHCE 2026 module to open/close
**ports**, allow predefined **services** (http, https, ssh), and manage the
**zones** (`public`, `internal`, `dmz`).

Module from the **`ansible.posix`** collection (not builtin): `ansible-galaxy
collection install ansible.posix`.

Critical options: **`service:`** (predefined service name) or **`port:`**
(format `8080/tcp`), **`state:`** (`enabled` / `disabled`), **`permanent: true`**
+ **`immediate: true`** (otherwise the classic trap), **`zone:`**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Allow** a predefined service (http, https, ssh) with `service:`.
2. **Open** a custom port with `port:` (format `8080/tcp`).
3. **Understand** the **`permanent: true` + `immediate: true`** trap (and why
   both).
4. **Distinguish** the firewalld **zones** (`public`, `internal`, `dmz`).
5. **Reload** firewalld via `systemd_service:` when necessary.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install ansible.posix
ansible web1.lab -m ping
ansible web1.lab -b -m systemd_service -a "name=firewalld state=started enabled=true"
ansible web1.lab -b -m shell -a "firewall-cmd --remove-port=8080/tcp 2>/dev/null; firewall-cmd --remove-port=8443/tcp 2>/dev/null; firewall-cmd --remove-service=https 2>/dev/null; firewall-cmd --runtime-to-permanent; true"
```

## 📚 Exercise 1 — The `permanent` vs `immediate` trap

`firewalld` distinguishes **two states**:

- **runtime**: rules active **now** (lost at reboot).
- **permanent**: rules persisted in `/etc/firewalld/`, **loaded at reboot**.

Without `permanent:`, you open now but lose it at reboot. Without
`immediate:` (with `permanent: true`), you persist but **nothing is applied
now**.

```yaml
# ❌ Trap: opens now, lost at reboot
- ansible.posix.firewalld:
    service: http
    state: enabled
    # No permanent → runtime only

# ❌ Trap: persists but not applied now
- ansible.posix.firewalld:
    service: http
    state: enabled
    permanent: true
    # No immediate → reload needed to apply

# ✅ Good: applies now AND persists
- ansible.posix.firewalld:
    service: http
    state: enabled
    permanent: true
    immediate: true
```

**Absolute rule**: **always** set `permanent: true` + `immediate: true`.

## 📚 Exercise 2 — Allow a predefined service

Create `lab.yml`:

```yaml
---
- name: Demo firewalld
  hosts: web1.lab
  become: true
  tasks:
    - name: Autoriser HTTP (service predefini)
      ansible.posix.firewalld:
        service: http
        state: enabled
        permanent: true
        immediate: true

    - name: Autoriser HTTPS
      ansible.posix.firewalld:
        service: https
        state: enabled
        permanent: true
        immediate: true

    - name: Lister les services autorises
      ansible.builtin.command: firewall-cmd --list-services
      register: fw_services
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        var: fw_services.stdout
        # → "ssh dhcpv6-client cockpit http https"
```

**Run it**:

```bash
ansible-playbook labs/modules-rhel/firewalld/lab.yml
```

🔍 **Observation**: `http` and `https` are added to the list of allowed
services. **Idempotence**: 2nd run → `changed=0`.

`firewall-cmd --get-services` lists all the available predefined services
(more than 100). Prefer a service over a port when possible: the intent is
clearer (`http` rather than `80/tcp`).

## 📚 Exercise 3 — Open a custom port

```yaml
- name: Ouvrir le port 8080/tcp (app custom)
  ansible.posix.firewalld:
    port: 8080/tcp
    state: enabled
    permanent: true
    immediate: true

- name: Ouvrir le port 8443/tcp (HTTPS custom)
  ansible.posix.firewalld:
    port: 8443/tcp
    state: enabled
    permanent: true
    immediate: true
```

**Format**: `<port>/<protocol>`: `tcp`, `udp`. For ranges: `8000-8100/tcp`.

**When to use `port:` rather than `service:`**:

- Custom app with no predefined service.
- Non-standard port (8080 instead of 80).
- Internal stack with private ports (Prometheus 9090, Grafana 3000, etc.).

## 📚 Exercise 4 — firewalld zones

```yaml
- name: Autoriser SSH dans la zone internal uniquement
  ansible.posix.firewalld:
    service: ssh
    zone: internal
    state: enabled
    permanent: true
    immediate: true

- name: Bloquer SSH dans la zone public
  ansible.posix.firewalld:
    service: ssh
    zone: public
    state: disabled
    permanent: true
    immediate: true
```

🔍 **Observation**: firewalld lets you **segment** rules by zone.
Use case: a multi-interface server (eth0 public, eth1 internal) with
different rules per interface.

**Default zones** on RHEL: `public` (most of the traffic), `internal`,
`trusted`, `dmz`, `block`, `drop`.

`firewall-cmd --get-default-zone` shows the default zone. To change it:

```yaml
- name: Changer la zone par defaut
  ansible.builtin.command: firewall-cmd --set-default-zone=internal
  changed_when: true
```

## 📚 Exercise 5 — Removing a rule

```yaml
- name: Retirer le port 8080
  ansible.posix.firewalld:
    port: 8080/tcp
    state: disabled
    permanent: true
    immediate: true
```

There is no `state: absent` for firewalld: it is `state: disabled`. The rule is
removed from the permanent files and from the runtime rules.

## 📚 Exercise 6 — Complete pattern: web stack

```yaml
- name: Stack web complete
  hosts: web1.lab
  become: true
  tasks:
    - name: Installer nginx
      ansible.builtin.dnf:
        name: nginx
        state: present

    - name: Demarrer nginx
      ansible.builtin.systemd_service:
        name: nginx
        state: started
        enabled: true

    - name: Ouvrir HTTP et HTTPS
      ansible.posix.firewalld:
        service: "{{ item }}"
        state: enabled
        permanent: true
        immediate: true
      loop: [http, https]
```

🔍 **Observation**: `loop:` on the service lets you open several ports in
one task. **Order**: install → start → open the firewall (otherwise the
service would be unreachable during the configuration).

## 📚 Exercise 7 — The trap: firewalld disabled

If firewalld is **not started**, the module **fails**:

```yaml
- name: Tenter d ouvrir un port
  ansible.posix.firewalld:
    port: 8080/tcp
    state: enabled
    permanent: true
    immediate: true
```

Error: `firewalld is not running`.

**Solution**: start firewalld first:

```yaml
- name: S assurer que firewalld tourne
  ansible.builtin.systemd_service:
    name: firewalld
    state: started
    enabled: true

- name: Maintenant on peut ouvrir un port
  ansible.posix.firewalld:
    port: 8080/tcp
    state: enabled
    permanent: true
    immediate: true
```

On minimal Docker images or custom installs, firewalld may be absent
or replaced by `iptables`/`nftables`. The module assumes firewalld.

## 🔍 Observations to note

- **Module `ansible.posix.firewalld:`** (not builtin, collection required).
- **`permanent: true` + `immediate: true`** = golden rule, always both.
- **`service:`** > **`port:`** when a predefined service exists (readability).
- **`zone:`** to segment rules by interface.
- **`state: disabled`** to remove (not `absent`).
- **firewalld must be running** (`systemd_service:`) before the module.

## 🤔 Reflection questions

1. You open port 8080 with **only `permanent: true`**. At the next
   `firewall-cmd --list-ports`, does the port appear? And after a reboot?

2. You have 50 webservers and you want to **close SSH from the internet**
   (zone `public`) while **keeping it open from the LAN** (zone `internal`).
   Which pattern?

3. Why is `firewalld` preferred over direct `iptables` on RHEL 8+?
   (hint: richness of the rules, persistence, rich-rules).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Rich rules**: advanced rules (limit-rate, log, masquerade) via
  the module's `rich_rule:` parameter.
- **Custom service**: create a custom firewalld service via `template:` on
  `/etc/firewalld/services/<name>.xml`, then `firewalld: service:` on it.
- **`source:`**: allow only from an IP or a range
  (`source: 192.168.1.0/24` + `service: ssh`).
- **`masquerade: true`**: enable NAT/SNAT (useful for a Linux router or
  a DMZ zone).
- **Lab 45 (selinux)**: complement the firewall with SELinux contexts for
  complete security.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-rhel/firewalld/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-rhel/firewalld/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-rhel/firewalld/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
