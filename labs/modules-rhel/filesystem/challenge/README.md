# Challenge `filesystem:`

## Statement

On **db1.lab**, the secondary disk `/dev/vdb` is already partitioned into 2
by the lab setup: `/dev/vdb1` (1 GiB) and `/dev/vdb2` (the rest).
Write `solution.yml` that brings the machine into this state:

1. `/dev/vdb2` carries an **xfs** filesystem.
2. `/dev/vdb1` is formatted as **swap**.
3. The swap is **active immediately** (`swapon --show` lists it) and
   written into `/etc/fstab` to survive a reboot.
4. `/dev/vdb2` is **mounted on `/mnt/data`**, with its own fstab entry.
5. A 2nd run of the playbook changes nothing (idempotent).

> 🎯 **No skeleton here, on purpose.** By this point you have written enough
> playbooks to start from a blank file, and that is exactly what the EX294
> asks: the exam hands you no canvas. The hints below target the traps of
> this module, not the YAML syntax.

## Success criteria

> ⏱️ **One test reboots db1** (about 90 s). It is marked `slow`, and it is
> there on purpose: persistence after a restart is the trap that fails RHCSA
> and RHCE candidates, and reading the config file proves nothing about it.
> While you iterate, you can leave it out:
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/filesystem/challenge/tests/
> ```
>
> Run the full suite at least once before considering the challenge done.

- `blkid /dev/vdb1` returns `TYPE="swap"`, `blkid /dev/vdb2` returns `TYPE="xfs"`.
- `swapon --show` returns `/dev/vdb1`.
- `mount | grep /mnt/data` shows `/dev/vdb2 on /mnt/data type xfs`.
- `cat /etc/fstab` contains both entries (mount and swap).
- 2nd run of the playbook: `changed: 0`.

## 🧩 Stuck?

```bash
dsoxlab hint modules-rhel-filesystem
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.
