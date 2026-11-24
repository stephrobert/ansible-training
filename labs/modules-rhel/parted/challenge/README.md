# Lay out the new disk before the storage team asks for it

## The situation

A second disk has just been attached to **db1.lab** and it arrives raw: no
label, no partition. The target layout is settled and comes from the
architecture: a small EFI boot partition, a fixed-size partition for a
filesystem, and everything left over handed to LVM so the volumes can grow
later. What matters as much as the layout is that this playbook will run again,
on this host and on the next twenty: **a partitioning tool that reruns is a
tool that destroys data**, unless it recognizes what already exists.

Your mission:

1. From **control-node.lab**, put a **GPT label** on the new disk of
   **db1.lab**, then carve the **500 MiB boot partition** with the flags an EFI
   partition needs.
2. Add the **4 GiB partition** meant for a filesystem, chained right after the
   first one with no gap and no overlap.
3. Give the **rest of the disk** to a third partition flagged for LVM, without
   hardcoding a size that would break on a differently sized disk.
4. Prove the **idempotence**: the second run must report `changed: 0`, and
   display the resulting table with its flags.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-parted/ (in French)

## Challenge `parted:`

### Statement

On **db1.lab** with a secondary disk **`/dev/vdb`**, write
`solution.yml` that:

1. Creates 3 GPT partitions on `/dev/vdb`:
   - `vdb1`: 500 MiB, flag `[boot, esp]`.
   - `vdb2`: 4 GiB, no particular flag (for ext4).
   - `vdb3`: rest of the disk, flag `[lvm]`.
2. Checks idempotence with a 2nd run.
3. Inspects the final table and displays it via `debug`.

> 🎯 **No skeleton here, on purpose.** By this point you have written enough
> playbooks to start from a blank file, and that is exactly what the EX294
> asks: the exam hands you no canvas. The hints below target the traps of
> this module, not the YAML syntax.

### Success criteria

- `lsblk /dev/vdb` shows 3 partitions with the right sizes.
- 2nd run of the playbook → **`changed: 0`** (idempotent).
- The `debug` displays the 3 partitions with their respective flags.

### 🧩 Stuck?

```bash
dsoxlab hint modules-rhel-parted
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.
