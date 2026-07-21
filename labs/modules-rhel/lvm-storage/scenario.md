# Context — Build storage that can grow without a maintenance window

The last outage on **db1.lab** taught the lesson the hard way: the data
partition was full, and enlarging a raw partition meant unmounting, resizing
and praying. The architecture team settled the matter for the next volume, LVM,
precisely so tomorrow's growth costs one command instead of a Sunday night. The
spare disk is attached and raw. You build the whole chain from
**control-node.lab**, from the physical volume up to the mounted volume, on a
playbook the fleet will replay.

Your mission:

1. On **db1.lab**, turn the **spare disk into a physical volume** and pool it
   into a **volume group**, in the single step the dedicated module offers.
2. Carve a **logical volume** out of that group, leaving room in the pool for
   the growth this whole setup exists for.
3. **Format** the logical volume in xfs and **mount it through fstab**, with the
   option that spares the disk its access-time writes. A volume mounted by hand
   is gone at the next reboot, silently.
4. Confirm the second run reports **`changed: 0`**.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/lvm-storage/
