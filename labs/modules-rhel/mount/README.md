# Lab 47 — Module `mount:` (manage fstab and mounts)

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

🔗 [**Ansible mount module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-mount/)

`ansible.posix.mount:` manages **Linux mount points**: add a line
in `/etc/fstab`, mount immediately, unmount, manage the mount options.
It is the #1 RHCE 2026 module for **persistent disks**: NFS volumes,
dedicated data disks, swap files.

Module from the **`ansible.posix`** collection. Critical options: **`path:`** (mount
point), **`src:`** (device or source), **`fstype:`** (`xfs`, `ext4`, `nfs`),
**`opts:`** (mount options), **`state:`** (`mounted`, `unmounted`, `present`,
`absent`, `remounted`).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Understand** the **5 values of `state:`**: `mounted`, `unmounted`,
   `present`, `absent`, `remounted`.
2. **Distinguish** an **fstab-only** entry from an **active mount** + fstab.
3. **Mount** a loop device (image file) to simulate a dedicated disk.
4. **Configure** classic mount options: `noatime`, `nodev`, `nosuid`.
5. **Diagnose** a mount that does not survive the reboot.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install ansible.posix
ansible db1.lab -m ping

# Clean up any previous lab
ansible db1.lab -b -m shell -a "umount /mnt/lab-data 2>/dev/null; rm -rf /mnt/lab-data /opt/lab-disk.img; sed -i '/lab-data/d' /etc/fstab; true"
```

## 📚 Exercise 1 — Understand the 5 values of `state:`

| `state:` | Effect on `/etc/fstab` | Runtime effect |
|---|---|---|
| `mounted` | Adds/updates the line | **Mounts** the filesystem now |
| `unmounted` | **Does not touch** fstab | **Unmounts** now |
| `present` | Adds/updates the line | **Does not mount** (fstab entry only) |
| `absent` | **Removes** the line | **Unmounts** if mounted |
| `remounted` | Does not touch fstab | **Remounts** (useful after an options change) |

🔍 **Use cases**:

- `mounted` (the most common): configure a permanent volume with immediate mount.
- `present`: prepare fstab **before** a reboot (deferred mount).
- `unmounted`: unmount without touching fstab (debug, maintenance).
- `absent`: complete removal (unmount + remove from fstab).
- `remounted`: apply an options change without fully unmounting.

## 📚 Exercise 2 — Create a loop device to simulate a disk

On a lab without a secondary disk, you can **create an image file** and expose it
as a block device via `losetup`. This is the universal trick to test `mount:`,
LVM, parted, etc.

```yaml
---
- name: Demo mount avec loop device
  hosts: db1.lab
  become: true
  tasks:
    - name: Creer un fichier image de 100M
      ansible.builtin.command:
        cmd: dd if=/dev/zero of=/opt/lab-disk.img bs=1M count=100
        creates: /opt/lab-disk.img

    - name: Formater en ext4
      community.general.filesystem:
        fstype: ext4
        dev: /opt/lab-disk.img

    - name: Creer le point de montage
      ansible.builtin.file:
        path: /mnt/lab-data
        state: directory
        mode: "0755"
```

🔍 **Observation**:

- **`creates:`** makes `dd` idempotent (skip if the file exists).
- The file `/opt/lab-disk.img` can be mounted **directly** via `mount`
  with the `loop` option (or `losetup`).
- **`community.general.filesystem:`** creates the filesystem on the file, covered
  in detail in lab 48.

## 📚 Exercise 3 — Mount with `state: mounted`

```yaml
- name: Monter le loop device sur /mnt/lab-data
  ansible.posix.mount:
    path: /mnt/lab-data
    src: /opt/lab-disk.img
    fstype: ext4
    opts: loop,defaults,noatime
    state: mounted
```

**Run it**:

```bash
ansible-playbook labs/modules-rhel/mount/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'df -h /mnt/lab-data && grep lab-data /etc/fstab'
```

🔍 **Observation**:

- `df -h` shows `/mnt/lab-data` mounted with ~95M available.
- `/etc/fstab` contains the line:

  ```text
  /opt/lab-disk.img  /mnt/lab-data  ext4  loop,defaults,noatime  0  0
  ```

- 2nd run → `changed=0` (idempotent: entry already present, already mounted).

Common **`opts:`**:

| Option | Effect |
|---|---|
| `defaults` | Default combination (`rw,suid,dev,exec,auto,nouser,async`) |
| `noatime` | No access-time update → fewer writes (perf) |
| `nodev` | No special files (devices), security |
| `nosuid` | Ignores setuid bits, security |
| `noexec` | No binary execution, security (`/tmp`, `/var/log`) |
| `loop` | For image files (auto `losetup` association) |
| `_netdev` | Network filesystem (NFS, SMB), wait for the network at boot |

## 📚 Exercise 4 — `state: present` vs `state: mounted`

```yaml
- name: Ajouter dans fstab SANS monter maintenant
  ansible.posix.mount:
    path: /mnt/lab-data
    src: /opt/lab-disk.img
    fstype: ext4
    opts: loop,defaults
    state: present
```

🔍 **Observation**:

- **`/etc/fstab`** is updated.
- **But the filesystem is NOT mounted** now.
- At the next reboot (or `mount -a`), the filesystem will be mounted automatically.

**Use cases**:

- Prepare the config in advance, mount manually afterwards.
- Network configs (`_netdev`) that cannot be mounted until the network is up.

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'mount -a && df -h /mnt/lab-data'
```

## 📚 Exercise 5 — Unmount and removal

```yaml
# Unmount without touching fstab
- name: Demonter pour maintenance
  ansible.posix.mount:
    path: /mnt/lab-data
    state: unmounted

# Complete removal (unmount + remove from fstab)
- name: Retrait complet
  ansible.posix.mount:
    path: /mnt/lab-data
    state: absent
```

🔍 **Observation**:

- **`state: unmounted`**: `umount /mnt/lab-data` but the fstab entry stays. At
  the next reboot, it remounts.
- **`state: absent`**: `umount` + removal of the fstab line. For a permanent
  removal.

**Trap**: if a process is using the filesystem (`lsof | grep /mnt/lab-data`),
the unmount fails with `device is busy`. Solution: kill the processes or
force with `force: true` (dangerous, risk of corruption).

## 📚 Exercise 6 — NFS pattern (network filesystem)

```yaml
- name: Monter un partage NFS
  ansible.posix.mount:
    path: /mnt/shared
    src: nfs-server.lab:/exports/shared
    fstype: nfs
    opts: rw,sync,hard,intr,_netdev
    state: mounted
```

**Critical NFS options**:

- **`_netdev`**: tells systemd to wait for the network before mounting
  (otherwise failure at boot).
- **`hard`**: retry indefinitely on a network outage (`soft` = failure after
  timeout, risk of corruption).
- **`intr`**: lets you interrupt blocked operations with `Ctrl+C`.
- **`rsize=`** / **`wsize=`**: buffer size (defaults usually OK).

**Security**: for NFS exposed on the Internet (not recommended), add `nosuid,nodev`.

## 📚 Exercise 7 — The trap: broken fstab entry

If you add an **invalid** fstab line, the **next reboot fails** with
a systemd drop-shell (`emergency mode`). The server is **unreachable over SSH**.

**Mitigation**:

```yaml
- name: Ajouter une entree (testable avant reboot)
  ansible.posix.mount:
    path: /mnt/critical
    src: /dev/critical-disk
    fstype: xfs
    opts: defaults
    state: present   # NOT mounted

- name: Tester avec mount -a (simule un reboot)
  ansible.builtin.command: mount -a
  changed_when: false
```

`mount -a` reads `/etc/fstab` and tries to mount everything. If an entry is
broken, you see the error **now**, not after a reboot.

**`backup: true`** on the module makes a backup of fstab before modification:

```yaml
- ansible.posix.mount:
    path: /mnt/lab-data
    src: /opt/lab-disk.img
    fstype: ext4
    state: mounted
    backup: true
```

→ Backup `/etc/fstab.<timestamp>~` created before modification.

## 🔍 Observations to note

- **5 values of `state:`**: `mounted`, `unmounted`, `present`, `absent`, `remounted`.
- **`mounted`** = mount now + fstab (the most common).
- **`present`** = fstab only, no mount (preparation).
- **`opts:`**: `noatime`, `nodev`, `nosuid` for security; `loop` for image files;
  `_netdev` for network.
- **NFS**: `hard,intr,_netdev` is the minimum.
- **Test `mount -a`** before a reboot to validate fstab.
- **`backup: true`** = free safety net on fstab.

## 🤔 Reflection questions

1. You want to mount a disk **only at boot** (not immediately). Which
   `state:`? How do you **test** that it will work at reboot without rebooting?

2. Difference between the module's `mount` and the shell command `mount`. Why
   does the **command** not modify `/etc/fstab` automatically?

3. You mount `/var/log` with `noexec`. What is the **impact** on the services
   that write into `/var/log/`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`bind` mount**: mount a directory onto another (`mount --bind /src /dst`).
  Useful to expose a subtree in a chroot or a container.
- **`tmpfs`**: filesystem in RAM (`fstype: tmpfs`). Ideal for a fast `/tmp`
  or volatile caches.
- **`/proc/mounts`** vs **`/etc/mtab`**: `/proc/mounts` is the current kernel state
  (authoritative). The module can read either one.
- **systemd `.mount` units**: modern alternative to fstab. Not handled by
  `mount:` but by `template:` on `/etc/systemd/system/<directory>.mount`.
- **Lab 48 (lvm-storage)**: create a PV/VG/LV on this lab's loop device, for
  extensible storage.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-rhel/mount/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-rhel/mount/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-rhel/mount/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
