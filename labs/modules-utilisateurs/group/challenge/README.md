# 🎯 Challenge — 3 groups with forced GIDs + 1 system group

## ✅ Objective

On **db1.lab**, create 4 groups via `ansible.builtin.group`, including 3 with an
**explicit GID** (for multi-host consistency) and 1 **system** group
(GID < 1000 auto-assigned by the system).

## 🧩 Specifications

| Name | GID | Type |
| --- | --- | --- |
| `rhce-shared` | **4000** | standard, forced GID |
| `rhce-admins` | **4001** | standard, forced GID |
| `rhce-readonly` | **4002** | standard, forced GID |
| `myapp-system` | (auto < 1000) | **system** |

> 💡 **Why force the GIDs?** On a multi-host fleet (NFS, shared containers…),
> the file permissions are stored **by GID**, not by group name. If
> `rhce-shared` has GID 4000 on one host and 1010 on another, the ACLs become
> inconsistent.

## 🧩 Skeleton

```yaml
---
- name: Challenge - 3 groupes RHCE + 1 système
  hosts: db1.lab
  become: true

  tasks:
    - name: Groupes RHCE avec GIDs forcés
      ansible.builtin.group:
        name: ???
        gid: ???
        state: present
      loop:
        - { name: rhce-shared, gid: 4000 }
        - { name: rhce-admins, gid: 4001 }
        - { name: rhce-readonly, gid: 4002 }
      # Already filled in: loop_control only changes what Ansible PRINTS
      # for each iteration (the item's name rather than the whole
      # dictionary). It is not the subject of this lab, and no test checks it.
      loop_control:
        label: "{{ item.name }}"

    - name: Groupe système myapp-system (GID < 1000)
      ansible.builtin.group:
        name: ???
        system: ???
        state: present
```

> 💡 **Traps**:
>
> - **`system: true`** creates a group with GID < 1000 (system range).
>   Convention for groups tied to services/daemons.
> - **explicit `gid:`**: for reproducibility, fix the GID. Without it,
>   `useradd` picks the next available one, which can vary between VMs.
> - **`local: true`**: forces the creation in `/etc/group` even if LDAP
>   is configured as the NSS source. Otherwise, the group can "exist" via
>   LDAP but not locally.
> - **Deleting a group in use**: `state: absent` fails if
>   users have this group as primary. Delete the users first.

## 🚀 Run

```bash
ansible-playbook labs/modules-utilisateurs/group/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "getent group rhce-shared rhce-admins rhce-readonly myapp-system"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-utilisateurs/group/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-utilisateurs-group
```

## 💡 Going further

- **GID conflict**: if you run on a host where GID 4000 is already taken by
  another group, the task fails. Demonstrate it by manually placing a
  `groupadd -g 4000 autre-groupe` beforehand.
- **`local: true`**: creates the group locally (`/etc/group`) even if the host
  uses a remote auth system (LDAP, SSSD).
- **Lint**:

   ```bash
   ansible-lint labs/modules-utilisateurs/group/challenge/solution.yml
   ```
