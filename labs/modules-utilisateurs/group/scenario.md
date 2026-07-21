# Context — Align the group numbering before mounting the NFS share

The team is about to share a volume between several hosts, and the first test
went badly: a file written on one server came back unreadable on the next.
Cause found, and it is textbook. The groups were created host by host with
whatever GID the system handed out, so the same group name carries two
different numbers, and the filesystem stores rights **by GID**, never by name.
Before the share goes live, the numbering gets frozen from **control-node.lab**.

Your mission:

1. Create the three project groups on **db1.lab** with their **explicit GIDs**
   (4000, 4001, 4002), so the numbering is reproducible on every host of the
   fleet.
2. Drive the three creations from a **single task**, not by copying and pasting
   the same block three times.
3. Add the application's **system group**, which belongs in the reserved range
   below 1000 and must let the system assign its own number.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-group/
