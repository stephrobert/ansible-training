# 🎯 Challenge — Firewalld for a web stack

## ✅ Objective

On **web1.lab**, configure **firewalld** to expose a web stack:

- **2 predefined services**: `http` (80), `https` (443)
- **2 custom ports**: `8080/tcp` (dev app), `8443/tcp` (dev app TLS)

All the rules must be **persistent** (`permanent: true`) **AND**
**active immediately** (`immediate: true`).

## 🧩 Why `permanent` AND `immediate`?

| Combination | Effect |
| --- | --- |
| `permanent: true` alone | The rule is written into the persistent config, **but not active**. It needs a `firewall-cmd --reload` to apply. |
| `immediate: true` alone | The rule is active now, **but lost at reboot**. |
| **Both** | Active now **and** persistent, which is what you want almost always. |

## 🧩 Skeleton

```yaml
---
- name: Challenge - firewalld web stack
  hosts: web1.lab
  become: true

  tasks:
    - name: Installer firewalld
      ansible.builtin.dnf:
        name: ???
        state: present

    - name: Démarrer et activer firewalld
      ansible.builtin.systemd_service:
        name: ???
        state: ???
        enabled: ???

    - name: Autoriser http + https (services prédéfinis)
      ansible.posix.firewalld:
        service: ???
        state: enabled
        permanent: ???
        immediate: ???
        zone: public
      loop: ???

    - name: Ouvrir les ports custom 8080/tcp + 8443/tcp
      ansible.posix.firewalld:
        port: ???
        state: enabled
        permanent: ???
        immediate: ???
        zone: public
      loop:
        - 8080/tcp
        - 8443/tcp
```

> 💡 **Traps**:
>
> - **`permanent: true` + `immediate: true`** together: rule
>   persistent across reboot AND active now. **Always** both for
>   a normal lab/prod.
> - **`permanent` alone**: modifies only the persistent config,
>   not the runtime table. It needs a `firewall-cmd --reload` afterwards.
> - **`zone:`**: without it, uses the default zone (`public` on AlmaLinux).
>   To compartmentalize, use `internal`, `dmz`, `trusted` depending on the
>   topology.
> - **`service:` vs `port:`**: prefer `service: http` (more readable,
>   portable) rather than `port: 80/tcp`. The service is defined in
>   `/usr/lib/firewalld/services/`.

## 🚀 Run

```bash
ansible-playbook labs/modules-rhel/firewalld/challenge/solution.yml
ansible web1.lab -b -m ansible.builtin.command -a "firewall-cmd --list-all"
```

🔍 **Manual checks**:

```bash
# Runtime (--query-service)
ansible web1.lab -b -m ansible.builtin.shell -a "firewall-cmd --query-service=http && firewall-cmd --query-service=https"
# Permanent
ansible web1.lab -b -m ansible.builtin.shell -a "firewall-cmd --permanent --query-port=8080/tcp && firewall-cmd --permanent --query-port=8443/tcp"
```

## 🧪 Automated validation

> ⏱️ **One test reboots db1** (about 90 s). It is marked `slow`, and it is
> there on purpose: persistence after a restart is the trap that fails RHCSA
> and RHCE candidates, and reading the config file proves nothing about it.
> While you iterate, you can leave it out:
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/firewalld/challenge/tests/
> ```
>
> Run the full suite at least once before considering the challenge done.

```bash
pytest -v labs/modules-rhel/firewalld/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-rhel-firewalld
```

## 💡 Going further

- **Creating a custom zone**: `zone: dmz` accepts an existing zone
  but does not create it. To create one, use `community.general.firewalld_info`
  or a `/etc/firewalld/zones/<zone>.xml` file via `template:`.
- **Rich rules**: `rich_rule:` lets you filter by source IP, do
  rate-limits, etc.
- **`source:`**: allow a subnet instead of a service
  (`source: 10.10.20.0/24`).
- **Lint**:

   ```bash
   ansible-lint labs/modules-rhel/firewalld/challenge/solution.yml
   ```
