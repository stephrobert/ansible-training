# 🎯 Challenge — Drive `chronyd` with the `timesync` system role

## ✅ Objective

Write `challenge/solution.yml`: **one play** on db1.lab that consumes the
system role **`fedora.linux_system_roles.timesync`** and passes it the compliance
intention as variables.

The tests do not re-read your configuration: they check the **state of
db1.lab**, including what `chronyd` really loaded **in memory**. A
correct file on disk with a daemon still running on the old
configuration is a failure.

> ⚠️ **The only prohibition of the lab**: do not write `/etc/chrony.conf` yourself.
> Neither `copy`, nor `template`, nor `lineinfile`, nor `blockinfile`. Everything goes through
> the role's variables. A test parses your YAML and requires the role in FQCN in
> the play's `roles:` list.

## 🧩 Expected contract

### The three NTP servers

| Server | Requested options |
| --- | --- |
| `0.fr.pool.ntp.org` | `iburst`, **preferred source** |
| `1.fr.pool.ntp.org` | `iburst` |
| `2.fr.pool.ntp.org` | `iburst`, **maximum polling interval of 10** |

Reminder: each entry of `timesync_ntp_servers` is a **dictionary**, whose
only required key is `hostname`. The other options are booleans or
integers bearing the name of the corresponding chrony directive.

### The two clock settings

- **Hard-correction threshold**: `0.1` second (the distribution is at `1.0`).
- **Minimum of concordant sources** before adjustment: `2` (the distribution
  is at `1`).

### What must disappear

- The distribution's **`pool`** directive.
- The **`sourcedir`** directive, which let the DHCP inject its servers.

Those two go away **on their own** if you did the rest correctly:
the role **regenerates** the file instead of amending it. If they are still there,
it means something is writing alongside the role.

## 🧩 Skeleton

```yaml
---
- name: Converger la synchronisation horaire de db1
  hosts: ???
  become: true
  gather_facts: true
  vars:
    timesync_ntp_servers:
      - hostname: ???
        iburst: ???
        ???: true
      - hostname: ???
        iburst: ???
      - hostname: ???
        iburst: ???
        ???: 10
    timesync_step_threshold: ???
    timesync_min_sources: ???
  roles:
    - role: ???
```

> 💡 **Pitfalls**:
>
> - **The FQCN.** `timesync` alone does not resolve: the role lives in a
>   collection. It is `fedora.linux_system_roles.timesync`. On exam
>   day, on a RHEL control node, it will be
>   `redhat.rhel_system_roles.timesync`: same role, same variables, different
>   packaging.
> - **The option names.** They are not invented. They are in
>   `defaults/main.yml` and in the role's `README.md`:
>   `ls ~/.ansible/collections/ansible_collections/fedora/linux_system_roles/roles/timesync/`
> - **The restart is not your business.** The role notifies its own
>   handler. If you add a `systemd_service: state=restarted` "to be
>   safe", your play will no longer be idempotent and the idempotence test will say so.
> - **`0.1` is not `"0.1"`.** The threshold is a float.

## 🚀 Run

```bash
ansible-playbook labs/roles/system-roles/challenge/solution.yml
```

## 🧪 Validation

```bash
pytest -v labs/roles/system-roles/challenge/tests/
```

To see with your own eyes what the tests look at:

```bash
ssh db1.lab
sudo grep -vE '^\s*(#|$)' /etc/chrony.conf   # the active directives
sudo cat /etc/sysconfig/network              # PEERNTP=no
chronyc -N sources                           # what the daemon loaded
chronyc tracking                             # what the clock is locked onto
```

## 🧹 Reset

```bash
dsoxlab clean roles-system-roles
```

## 💡 Going further

- **Set `timesync_dhcp_ntp_servers: true`** and replay: `sourcedir`
  reappears, `PEERNTP=no` disappears. One variable, two files, zero line
  of configuration written.
- **Remove `timesync_min_sources`** and replay: the `minsources` directive
  disappears from the file. The role leaves no residue from your previous run,
  unlike a `lineinfile`.
- **`ansible-playbook --check --diff`**: the role displays the diff of the file
  it *would* have written. It is the configuration review that you cannot
  do with a `copy` of inline content.
- **`ansible-lint --profile production labs/roles/system-roles/challenge/solution.yml`**:
  expected output `Passed: 0 failure(s), 0 warning(s)`.
