# Context — "Show me what it will change, before it changes it"

The change advisory board asks the same question before every run on
**db1.lab**, and it is a fair one: *what exactly is this playbook going to
touch?* Last quarter a playbook rewrote a file under `/etc` nobody expected it
to touch, and "it should be fine" did not survive the post-mortem. New rule:
every change is rehearsed dry, its diff is read out loud, and only then does
the same playbook run for real.

You drill that workflow from **control-node.lab** on a harmless marker file.

Your mission:

1. Write a play that drops `/etc/lab-checkmode.txt` on `db1.lab`, mode `0644`,
   with a known content.
2. Run it **`--check --diff`** first: read the before/after block, then confirm
   on `db1.lab` that nothing was actually written.
3. Run it for real and check the diff matches exactly what the dry run
   announced.
4. Run it a third time: no diff, `changed=0`. Then learn which modules cannot
   simulate, and how to force a read-only task to run even in check mode.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/checkmode-diff/
