# Context — Pull EPEL tooling onto db1 without dragging the kernel along

The DBA wants two diagnostic tools on **db1.lab** to chase down a disk
saturation: a live process viewer and a directory usage explorer. Neither ships
in the base AlmaLinux repositories, they live in EPEL. The last colleague who
enabled a third-party repo also let a metapackage pull a fresh kernel through,
and the database rebooted onto an untested kernel. That will not happen twice.
You work from **control-node.lab**, and the transaction stays under control.

Your mission:

1. Add the **EPEL** repository to **db1.lab** through its official release
   package, rather than hand-writing a `.repo` file.
2. Install the two diagnostic tools by **enabling EPEL explicitly** for that
   transaction and **refreshing the metadata cache** beforehand.
3. **Exclude every kernel package** from the transaction: no dependency may
   bump the kernel of a production database by side effect.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-dnf-options/
