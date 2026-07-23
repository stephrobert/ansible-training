# Context — Turn the partitioned disk into usable storage

The disk on **db1.lab** is partitioned but still useless: partitions without a
filesystem hold nothing. Two needs to cover. The data partition must carry the
filesystem the database vendor recommends for its large files, and the small
partition becomes the swap the box has been missing since the last OOM kill.
Both must come back **on their own after a reboot**: swap enabled by hand and a
volume mounted by hand both vanish at the next restart, silently.

Your mission:

1. From **control-node.lab**, create the **xfs filesystem** on the data
   partition of **db1.lab**, and prepare the small partition **as swap**.
2. **Activate the swap now** and register it in `/etc/fstab`, keeping in mind
   that swap is not mounted on a directory like an ordinary filesystem.
3. **Mount the data partition** on its mount point, with its own fstab entry.
4. Prove both: the swap shows up as active, the mount point reports xfs, and the
   second run reports `changed: 0`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-filesystem/
