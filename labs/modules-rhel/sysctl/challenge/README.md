# 🎯 Challenge — 4 sysctl parameters for hardening

## ✅ Objective

On **db1.lab**, configure **4 `sysctl` parameters** in a dedicated file
**`/etc/sysctl.d/99-rhce-lab.conf`**, and apply them immediately.

| Parameter | Value | Effect |
| --- | --- | --- |
| `net.ipv4.ip_forward` | `1` | Enables IPv4 routing (useful on a firewall/NAT) |
| `net.ipv4.tcp_syncookies` | `1` | Protection against SYN floods |
| `kernel.kptr_restrict` | `2` | Hides kernel pointers in `/proc` (hardening) |
| `vm.swappiness` | `10` | Prefers RAM over swap (perf) |

## 🧩 Hints

- `ansible.posix.sysctl` is the module to use.
- **`sysctl_file:`**: file where the value is written. If you omit it, the
  parameter is written into `/etc/sysctl.conf` (global file). Prefer a
  dedicated file `/etc/sysctl.d/99-<role>.conf` (Ansible-friendly,
  versionable).
- **`reload: true`**: applies immediately (`sysctl -p ...`). Without it, the
  value is only active **after a reboot**.

## 🧩 Skeleton

```yaml
---
- name: Challenge - sysctl 4 paramètres
  hosts: db1.lab
  become: true

  tasks:
    - name: Configurer 4 paramètres dans /etc/sysctl.d/99-rhce-lab.conf
      ansible.posix.sysctl:
        name: ???
        value: ???
        state: present
        sysctl_file: ???
        reload: ???
      loop:
        - { name: net.ipv4.ip_forward, value: '1' }
        - { name: net.ipv4.tcp_syncookies, value: '1' }
        - { name: kernel.kptr_restrict, value: '2' }
        - { name: vm.swappiness, value: '10' }
      # Already filled in: loop_control only changes what Ansible PRINTS
      # for each iteration (the item's name rather than the whole
      # dictionary). It is not the subject of this lab, and no test checks it.
      loop_control:
        label: "{{ item.name }}"
```

> 💡 **Quote the `value:`**: `'1'`, `'2'`, etc.: `sysctl` likes strings.

**Traps**:

> - **`sysctl_file:`**: by default `/etc/sysctl.conf` (deprecated on
>   RHEL 9+). Prefer `/etc/sysctl.d/<NN>-<topic>.conf` (priority
>   number 99 = read last).
> - **`reload: true`** (default): applies the new setting **now**
>   (not only to persistence). If `false`, a reboot or
>   `sysctl -p` is needed.
> - **`name:`** = sysctl key (`net.ipv4.ip_forward`). Dot-separated
>   format, **not** slash-separated (`/proc/sys/...`).
> - **Idempotence**: `sysctl:` compares the current value. If it
>   matches, `changed=0`. True for persistence AND runtime simultaneously.

## 🚀 Run

```bash
ansible-playbook labs/modules-rhel/sysctl/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/sysctl.d/99-rhce-lab.conf"
ansible db1.lab -m ansible.builtin.command -a "sysctl -n net.ipv4.ip_forward vm.swappiness"
```

## 🧪 Automated validation

> ⏱️ **One test reboots db1** (about 90 s). It is marked `slow`, and it is
> there on purpose: persistence after a restart is the trap that fails RHCSA
> and RHCE candidates, and reading the config file proves nothing about it.
> While you iterate, you can leave it out:
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/sysctl/challenge/tests/
> ```
>
> Run the full suite at least once before considering the challenge done.

```bash
pytest -v labs/modules-rhel/sysctl/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-rhel-sysctl
```

## 💡 Going further

- **`state: absent`**: removes the parameter from the file (but does **not**
  reset the runtime value: a reboot or an explicit sysctl will be needed).
- **Audit the active sysctl**: `sysctl -a | grep ip_forward` or
  `cat /proc/sys/...`.
- **CIS hardening pattern**: an Ansible role "cis-rhel-baseline" sets
  ~30 sysctl parameters. This is exactly the pattern to industrialize.
- **Lint**:

   ```bash
   ansible-lint labs/modules-rhel/sysctl/challenge/solution.yml
   ```
