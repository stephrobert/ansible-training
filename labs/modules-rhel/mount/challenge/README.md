# 🎯 Challenge — Mount a persistent loop device

## ✅ Objective

On **db1.lab**, create a `100M` image file, format it as `ext4`, and
**mount** it on `/mnt/lab-data` with an **`/etc/fstab` entry** (persistent
across reboot). The mount is **required** to carry the options
`loop,defaults,noatime,nodev,nosuid`: `loop` turns the image into a loop
device (this is what survives the reboot), `noatime` skips access-time
writes, and `nodev,nosuid` are the hardening options (no device nodes, no
setuid on this filesystem).

## 🧩 Steps

1. Create the image file **`/opt/lab-disk.img`** of 100 MB (use `dd` with
   `creates:` for idempotence).
2. **Format** as `ext4` via `community.general.filesystem`.
3. Create the **mount point** `/mnt/lab-data` (mode 0755).
4. **Mount** + write into **fstab** via `ansible.posix.mount` with
   `state: mounted` and `opts: loop,defaults,noatime,nodev,nosuid`.

## 🧩 Key modules

| Module | Role |
| --- | --- |
| `ansible.builtin.command` (with `creates:`) | Create the image idempotently |
| `community.general.filesystem` | Format (ext4, xfs, …) |
| `ansible.builtin.file` | Create the mount point |
| `ansible.posix.mount` | Mount + manage fstab |

## 🧩 Semantics of the mount module's `state:`

| `state:` | Effect |
| --- | --- |
| `present` | Writes into fstab, **does not mount** |
| `mounted` | Writes into fstab **AND** mounts now, which is what you want |
| `unmounted` | Unmounts, **keeps** the fstab line |
| `absent` | Unmounts **and** removes from fstab |

## 🧩 Mount options

This challenge **requires** `opts: loop,defaults,noatime,nodev,nosuid`
(comma-separated). Each one:

- `loop`: **required**, for an image file (turns `/opt/lab-disk.img` into
  a loop device, and this is what makes the mount survive a reboot).
- `defaults`: default set of options.
- `noatime`: **required**, does not record access times (perf).
- `nodev,nosuid`: **required** hardening (forbids devices and setuid on this FS).

The tests check that `noatime`, `nodev` and `nosuid` are active on the mount
(via `findmnt`) and still present after a reboot: omitting them fails the lab.

## 🧩 Skeleton

```yaml
---
- name: Challenge - mount loop device persistant
  hosts: db1.lab
  become: true

  tasks:
    - name: Créer le fichier image 100M
      ansible.builtin.command:
        cmd: ???
        creates: ???

    - name: Formater l'image en ext4
      community.general.filesystem:
        fstype: ???
        dev: ???

    - name: Créer le point de montage
      ansible.builtin.file:
        path: ???
        state: directory
        mode: "0755"

    - name: Monter + entrée fstab
      ansible.posix.mount:
        path: ???
        src: ???
        fstype: ???
        opts: ???
        state: ???
```

> 💡 **Traps**:
>
> - **`state:`**: `mounted` = `fstab` + mount now; `present` =
>   fstab only (no mount); `absent` = unmount + remove fstab.
>   For prod, **`mounted`** is the standard option.
> - **`opts:`** = fstab options (field 4). Comma-separated list, here
>   `loop,defaults,noatime,nodev,nosuid`. Without `loop` the image is not
>   turned into a loop device and the mount does not survive the reboot.
> - **`fstype: nfs`** requires `nfs-utils` on the managed node. Otherwise
>   it fails with "filesystem type not supported".
> - **`backup: true`** on `mount:`: backs up `fstab` before
>   modification, valuable in prod.

## 🚀 Run

```bash
ansible-playbook labs/modules-rhel/mount/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "df -h /mnt/lab-data"
ansible db1.lab -m ansible.builtin.command -a "grep lab-data /etc/fstab"
ansible db1.lab -m ansible.builtin.command -a "mount | grep lab-data"
```

## 🧪 Automated validation

> ⏱️ **One test reboots db1** (about 90 s). It is marked `slow`, and it is
> there on purpose: persistence after a restart is the trap that fails RHCSA
> and RHCE candidates, and reading the config file proves nothing about it.
> While you iterate, you can leave it out:
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/mount/challenge/tests/
> ```
>
> Run the full suite at least once before considering the challenge done.

```bash
pytest -v labs/modules-rhel/mount/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-rhel-mount
```

## 💡 Going further

- **`state: present`** alone: write into fstab without mounting (useful to
  pre-configure a host before a physical disk is plugged in later).
- **`backup: true`**: backs up `/etc/fstab` as `.bak` before modification.
- **Image-based pattern**: useful in dev to simulate a disk without
  hardware. In prod, you rather mount an LVM device (lab 48).
- **Lint**:

   ```bash
   ansible-lint labs/modules-rhel/mount/challenge/solution.yml
   ```
