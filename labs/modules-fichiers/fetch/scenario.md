# Context — Collect the OS inventory before the migration window

Management wants to know exactly which distribution release runs on each server
before signing off the migration plan, and "I checked, they're all the same"
does not count as evidence. You need the raw `/etc/os-release` of every managed
node, filed on **control-node.lab** under a predictable name, ready to diff and
to attach to the plan. Screenshots of SSH sessions are not an inventory: the
collection has to be replayable when the fleet grows.

Your mission:

1. Pull **`/etc/os-release`** from **web1.lab** and **db1.lab** back to the
   control node, each landing in a **flat file named after its short hostname**
   (no per-host subtree, no `.lab` suffix).
2. Tag **web1.lab** with a lab identity file, then bring that file back to the
   control node as well: the same play both pushes and retrieves.
3. Make the destination paths **derive from the inventory**, not from a
   hand-written list of hostnames.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-fetch/
