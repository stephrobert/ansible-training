# Context — Lay out the new disk before the storage team asks for it

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
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-parted/
