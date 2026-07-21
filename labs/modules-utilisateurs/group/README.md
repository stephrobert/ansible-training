# Lab 41 — `group:` module (manage Linux groups)

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

🔗 [**Ansible group module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-group/)

`ansible.builtin.group:` manages **Linux groups**: creation, deletion, forcing
the GID. Companion module of [`user:`](../user/): you
first create the groups, then attach the users.

Main options: **`name:`**, **`state:`**, **`gid:`**, **`system: true`** (for
system groups with GID < 1000).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** a simple group and a group with a **forced GID** (multi-host
   consistency).
2. **Distinguish** a user group (GID ≥ 1000) from a system group
   (`system: true`, GID < 1000).
3. **Delete** a group with `state: absent` (and its behavior when users are
   still part of it).
4. **Order** the tasks: create the **group before** the user that references it.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "for g in dev-team ops-team rhce-shared; do groupdel \$g 2>/dev/null; done; true"
```

## 📚 Exercise 1 — Basic creation

Create `lab.yml`:

```yaml
---
- name: Demo group simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer le groupe dev-team
      ansible.builtin.group:
        name: dev-team
        state: present

    - name: Verifier la creation
      ansible.builtin.command: getent group dev-team
      register: dev_team_check
      changed_when: false

    - name: Afficher l entree /etc/group
      ansible.builtin.debug:
        var: dev_team_check.stdout
        # → dev-team:x:1001:
```

**Run**:

```bash
ansible-playbook labs/modules-utilisateurs/group/lab.yml
```

🔍 **Observation**:

- 1st run: `changed=1`, `groupadd dev-team`.
- 2nd run: `changed=0`, already present.
- The **GID is auto-assigned** (first free one ≥ 1000).

## 📚 Exercise 2 — Forced GID (multi-host consistency)

```yaml
- name: Creer ops-team avec GID 3000 force
  ansible.builtin.group:
    name: ops-team
    gid: 3000
    state: present

- name: Creer rhce-shared avec GID 3001 force
  ansible.builtin.group:
    name: rhce-shared
    gid: 3001
    state: present
```

🔍 **Observation**: on 50 hosts, these groups will **always have the same GID**.
This is essential for:

- **NFS**: if a file belongs to `gid=3001` on the NFS server side, the client
  must also have `gid=3001` to be able to open it.
- **Containers**: volumes shared between host and container.
- **Audit**: compare the GIDs between hosts to detect a divergence.

**If the GID is already taken** by another group: the task is **failed**. No
silent collision.

## 📚 Exercise 3 — System group (GID < 1000)

```yaml
- name: Creer un groupe systeme (GID auto < 1000)
  ansible.builtin.group:
    name: myapp-system
    system: true
    state: present
```

🔍 **Observation**: `system: true` tells Ansible to **look for a GID < 1000** (by
RHEL convention for system groups). Without `system:`, the auto-assigned GID is
≥ 1000 (user group).

**Use case**: create an **application** group reserved for the daemon (nginx,
postgres, etc.) that must not be confused with a user group.

## 📚 Exercise 4 — Deletion (`state: absent`)

```yaml
- name: Supprimer le groupe dev-team
  ansible.builtin.group:
    name: dev-team
    state: absent
```

**Before the deletion**, create a user that uses this group:

```yaml
- name: Creer carl dans dev-team (avant la suppression)
  ansible.builtin.user:
    name: carl
    group: dev-team   # Primary group
```

**If you try to delete a group that is still the primary group** of a user, the
task is **failed**:

```text
groupdel: cannot remove the primary group of user 'carl'
```

🔍 **Observation**: system protection. To delete the group, you must **first
delete or reassign the user**.

```yaml
- name: Reassigner carl a un autre groupe primaire
  ansible.builtin.user:
    name: carl
    group: nogroup

- name: Maintenant on peut supprimer dev-team
  ansible.builtin.group:
    name: dev-team
    state: absent
```

## 📚 Exercise 5 — Ordering: group BEFORE user

Classic pattern: create the **group** first, **then** the users that reference it.

```yaml
- name: Step 1 — creer le groupe
  ansible.builtin.group:
    name: rhce-team
    gid: 5000
    state: present

- name: Step 2 — creer alice avec rhce-team comme primaire
  ansible.builtin.user:
    name: alice
    group: rhce-team   # The group MUST already exist
    state: present
```

🔍 **Observation**: if you invert the order, `user:` would create alice with a
`rhce-team` group **generated automatically** (auto-assigned GID). Then when
`group: gid: 5000` tries to create it, there is a **conflict** between the
requested GID (5000) and the generated one (1001 or other).

**Convention**: within the same play, **always** order:

1. `group:` (creation of the groups)
2. `user:` (creation of the users that use them)
3. `authorized_key:` (users' SSH keys, see lab 42)
4. `lineinfile:` or other (sudo config etc.)

## 📚 Exercise 6 — The trap: modifying the GID of an existing group

```yaml
- name: Tenter de changer le GID d ops-team
  ansible.builtin.group:
    name: ops-team
    gid: 3500   # Avant : 3000
```

🔍 **Observation**: the task **succeeds**, `groupmod -g 3500 ops-team`. But
**all the files** belonging to `gid=3000` are **now orphaned**:

```bash
# Before change
$ ls -la /home/alice/data
-rw-r--r-- 1 alice ops-team 0 ... data
$ stat -c '%g' /home/alice/data
3000  ← OK

# After change
$ ls -la /home/alice/data
-rw-r--r-- 1 alice 3000     0 ... data   # No more name!
```

**Solution**: **never** modify a group's GID in production. If necessary:

1. Delete the group.
2. Recreate it with the new GID.
3. **`chgrp -R`** on all the concerned files.

## 🔍 Observations to note

- **`name:`** = identification key.
- **`gid:`** forced for **multi-host consistency** (NFS, containers, audit).
- **`system: true`** = group with GID < 1000 (RHEL convention).
- **Deleting a user's primary group** → **failed**. Reassign first.
- **Order**: `group:` BEFORE the `user:` that references it.
- **Do not modify the GID** of an existing group, orphaned files.

## 🤔 Reflection questions

1. You have 10 users to create in `rhce-team`, plus 5 in `dev-team`, plus 3 in
   `ops-team`. Which pattern (`loop:` over `users` with a `groups` field, or
   separate plays)?

2. Why is `system: true` important for an application group (`nginx`,
   `postgres`)? What is the **concrete risk** of an application group with a
   GID ≥ 1000?

3. You want to **guarantee** that a group has a precise GID on 50 hosts. How do
   you articulate `group: gid:` with `failed_when:` to fail if the GID differs?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`local: true`**: force the creation in `/etc/group` even if the system uses
  NIS/LDAP. Useful on hosts integrated into a directory but that must have local
  groups.
- **`getent:` module**: retrieve a group's info from NSS (LDAP, AD, NIS) without
  depending on the local `/etc/group`.
- **`groupinstall` pattern**: for groups tied to DNF packages (`@web-server`),
  it is `dnf: name: '@web-server'` and not `group:`.
- **`group:` + `user:` + `authorized_key:` combination**: onboarding pattern for
  a new team member, see lab 42.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-utilisateurs/group/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-utilisateurs/group/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-utilisateurs/group/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
