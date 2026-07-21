# Context — Give the app a dedicated volume that comes back after a reboot

The application on **db1.lab** writes its data straight onto the root
filesystem, and one runaway log already filled the disk and stopped the system.
It needs its own space, isolated, but the physical disk is weeks away from
delivery. An image file mounted as a loop device buys the isolation now, without
waiting for hardware. The real requirement is the one everyone forgets: a
volume mounted by hand disappears at the next reboot, and the app restarts
writing onto the root filesystem without a word.

Your mission:

1. On **db1.lab**, create the **100 MB image file** in a way that a second run
   will not recreate, then **format it in ext4**.
2. Create the mount point, then **mount the image and register it in
   `/etc/fstab`** in one step: the state you pick decides whether the mount
   survives the reboot.
3. Pass the option that turns the image file into a usable device, and harden
   the volume so it can carry **no device nodes and no setuid binaries**.
4. Prove the persistence: the fstab entry is there and the volume is mounted
   right now.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-mount/
