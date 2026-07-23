# Context — Ship the team's shell aliases without wrecking the profile

The on-call team wants its usual shortcuts available on **db1.lab**: listing
files, checking git status, and above all seeing the open ports during an
incident without digging for the `ss` flags. A colleague already tried, pasting
the aliases by hand into a profile script, and re-pasted them at the next
change: the block now sits there three times. You take it over from
**control-node.lab**, with a playbook that owns its block and stops duplicating
it.

Your mission:

1. Create **`/etc/profile.d/aliases-rhce.sh`** on **db1.lab** (mode `0644`),
   the file does not exist yet.
2. Maintain the three team aliases inside it as a **single block framed by
   your own markers**, so the block is recognized and replaced rather than
   appended.
3. Prove the **idempotence**: after a second run, the opening marker must
   appear **exactly once** in the file.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-blockinfile/
