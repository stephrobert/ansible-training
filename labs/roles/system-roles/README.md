# Lab 99 — RHEL system roles: converge time with `timesync`

> 💡 **Landing directly on this lab without having done the previous ones?**
> Single prerequisite: the 4 lab VMs respond to the ping.

## 🧠 Recap

🔗 [**Ansible roles**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/)

"**Use RHEL system roles**" is an explicit objective of the **EX294** exam.
It is the only exam objective that this training addressed nowhere
before this lab.

A **system role** is a role written and maintained by Red Hat, shipped with the
distribution, that exposes a **stable variable interface** on top of a
subsystem whose configuration changes from one version to the next. You no
longer describe a file, you describe a **result**:

```yaml
- name: Converger l'heure
  hosts: db1.lab
  become: true
  vars:
    timesync_ntp_servers:
      - hostname: 0.fr.pool.ntp.org
        iburst: true
  roles:
    - role: fedora.linux_system_roles.timesync
```

The role handles the rest: detect whether the machine runs `chrony` or
`ntpd`, install the package, generate the file, disable the competing provider,
restart the daemon. The same play holds from RHEL 6 to RHEL 10.

## 📦 Package or collection? Both, and it is not the same thing

There are **two distributions of the same code** (the upstream project
[linux-system-roles](https://linux-system-roles.github.io/)):

| | Package `rhel-system-roles` | Collection `fedora.linux_system_roles` |
| --- | --- | --- |
| Origin | RHEL / AlmaLinux `appstream` repo | Ansible Galaxy |
| Installation | `dnf install rhel-system-roles` | `ansible-galaxy collection install` |
| Location | `/usr/share/ansible/roles/` and `/usr/share/ansible/collections/` | `~/.ansible/collections/` |
| Call name | `redhat.rhel_system_roles.timesync` | `fedora.linux_system_roles.timesync` |
| Support | Red Hat certified | community |
| **On exam day** | **it is this one** | absent |

**This lab uses the collection.** Two reasons, measurable:

1. **The package is not installable on this training's control
   node.** A role is resolved **where `ansible-playbook` runs**, never
   on the target. Here, `ansible-playbook` runs on your machine (Ubuntu in the
   test harness), which has neither `dnf` nor `rpm`: `/usr/share/ansible/roles/`
   will never exist there. The package **is** available for AlmaLinux
   (`dnf list --available rhel-system-roles` on db1.lab returns version
   1.120.5), but it would only serve a RHEL control node.
2. **It is the same code.** The collection installed here is at 1.121.0, the package
   AlmaLinux at 1.120.5: two packagings of the same upstream, one minor
   version apart.

> ⚠️ **On exam day**, the control node is a RHEL. The reflex is
> `dnf install rhel-system-roles`, then `redhat.rhel_system_roles.<role>`.
> **Only the prefix changes**, the variables are identical. What you
> learn here transposes as is.

Check what you have:

```bash
ansible-galaxy collection list fedora.linux_system_roles
ls ~/.ansible/collections/ansible_collections/fedora/linux_system_roles/roles/
```

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Find** the available system roles and **read** their interface
   (`defaults/main.yml`, the role's `README.md`).
2. **Consume** a system role in **FQCN** from a play.
3. Drive `chronyd` **through variables** (`timesync_ntp_servers`,
   `timesync_step_threshold`, `timesync_min_sources`) without ever touching
   `/etc/chrony.conf`.
4. **Prove** that the configuration is applied, by querying the daemon and
   not the file.
5. Tell the difference between the **package** and the **collection**, and know
   which one awaits you at the exam.

## 🔧 Preparation

```bash
ansible db1.lab -m ansible.builtin.ping
```

## 📚 Exercise 1 — The role's interface, before the role

A system role is read through its **defaults**: these are its public parameters.

```bash
cat ~/.ansible/collections/ansible_collections/fedora/linux_system_roles/roles/timesync/defaults/main.yml
```

```yaml
timesync_ntp_servers: []
timesync_ptp_domains: []
timesync_dhcp_ntp_servers: false
timesync_step_threshold: -1.0
timesync_min_sources: 1
timesync_ntp_provider: ""
```

🔍 **Observations**:

- **All the variables are prefixed `timesync_`.** It is the rule of system
  roles, and the reason why you can stack ten of them in a play without
  collision.
- **`timesync_ntp_provider: ""`**: empty means "figure it out". The role
  detects `chrony` or `ntpd` depending on what is installed.
- **`timesync_ntp_servers: []`**: a **list of dictionaries**, not of
  strings. Each entry carries a `hostname` and its options.

## 📚 Exercise 2 — The starting state of db1

```bash
ssh db1.lab
sudo grep -vE '^\s*(#|$)' /etc/chrony.conf
```

```text
pool 2.almalinux.pool.ntp.org iburst
sourcedir /run/chrony-dhcp
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
ntsdumpdir /var/lib/chrony
logdir /var/log/chrony
```

🔍 **Observations**:

- A **`pool`** (a single line, four sources behind it) and not `server` entries.
- **`sourcedir /run/chrony-dhcp`**: the DHCP client can inject its own
  NTP servers. For a compliance server, it is an open door.
- **`makestep 1.0 3`** and **no `minsources`**: these are the values of the
  distribution, not yours.

> ⚠️ **The shipped-file pitfall**: `/etc/chrony.conf` contains the line
> `#minsources 2`, **commented out**. A test that looked for the substring
> `minsources 2` in the file would be green before you even started.
> This lab's tests compare only **active lines**, by equality.

## 📚 Exercise 3 — An entry of `timesync_ntp_servers`

```yaml
timesync_ntp_servers:
  - hostname: 2.fr.pool.ntp.org
    iburst: true
    maxpoll: 10
```

becomes, in `/etc/chrony.conf`:

```text
server 2.fr.pool.ntp.org maxpoll 10 iburst
```

🔍 **Observation, and it is the heart of the lab**: **the order of the options in the
generated line is not that of your dictionary.** The role's template
emits them in its own order (`minpoll`, `maxpoll`, `nts`, `iburst`, `prefer`…).
You describe an **intention**; the syntax is the role's problem. This is
precisely what you buy by using a system role, and it is why
copying the result by hand is a contradiction.

Useful keys of an entry: `hostname` (required), `iburst`, `prefer`, `minpoll`,
`maxpoll`, `pool` (emits `pool` instead of `server`), `nts`, `trust`.

## 📚 Exercise 4 — What the role does beyond the file

Run the challenge play, then compare:

```bash
ssh db1.lab
sudo head -4 /etc/chrony.conf        # the role's signature
sudo cat /etc/sysconfig/network      # PEERNTP=no
chronyc -N sources                   # what the daemon REALLY loaded
```

🔍 **Three effects that are systematically forgotten when writing the file by
hand**:

1. **The signature.** The role opens the file with `# Ansible managed` then
   `# system_role:timesync`. That is what tells the next admin not to
   edit this file.
2. **`PEERNTP=no`** in `/etc/sysconfig/network`. Without it, the DHCP client
   reinjects its servers at the next lease and your compliance breaks
   silently, weeks later.
3. **The restart.** The role **notifies a handler** `Restart chronyd`.
   A file written without a restart changes nothing: `chronyd` still runs
   on the old configuration, and `chronyc` will tell you.

> 💡 **`chronyc` queries the daemon, not the disk.** It is the tool that
> distinguishes "I wrote a file" from "the machine is configured".

## 🔍 Observations to note

- A system role is **idempotent by construction**: replayed, it does not rewrite
  the file and does not restart the daemon. Check it, it is an RHCE
  criterion.
- **`gather_facts: true`** is not indispensable (the role collects the
  facts it needs itself), but keep the exam reflex.
- **Never define a `timesync_*` variable that you have not read**
  in `defaults/main.yml` or in the role's `README.md`: what is not
  in the interface is private and can change without notice.

## 🤔 Reflection questions

1. You set `timesync_ntp_provider: ntp` on a machine where only `chrony`
   is installed. What does the role do? (Hint: read the `Install ntp` task.)
2. Why does the role write `PEERNTP=no` when you did not
   ask it to? Which variable would set it back to `yes`?
3. You must apply `timesync` to 200 machines, 40 of which are RHEL 7.
   What does the role save you from writing?
4. On exam day, `dnf install rhel-system-roles` then
   `ansible-galaxy collection list`: where on the filesystem did the
   package place the collection, and why does Ansible find it without
   configuration?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **The other exam roles**: `firewall`, `selinux`, `storage`,
  `postfix`, `sshd`. All follow the same grammar: variable prefix,
  `defaults/main.yml` as the contract, idempotence.
- **`ansible-doc -t role -l fedora.linux_system_roles`**: the list of roles
  with their description, without leaving the terminal.
- **`timesync_ntp_ip_family: IPv4`**: forces `-4` in `chronyd`'s options.
  Look at what `/etc/sysconfig/chronyd` becomes.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile production labs/roles/system-roles/
```
