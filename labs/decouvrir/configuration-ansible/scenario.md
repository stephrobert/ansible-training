# Context — Whose ansible.cfg is actually running?

The same playbook takes four minutes for you and eleven for your colleague,
and neither of you can say which `ansible.cfg` Ansible really read: the one in
`/etc`, the one in the home directory, the one at the repo root, or an
environment variable silently overriding them all. Worse, nobody can tell
which task eats the eleven minutes. Guessing stops today.

You work from **control-node.lab** and keep your evidence on `db1.lab`.

Your mission:

1. Write a **project `ansible.cfg`** that raises parallelism to **`forks = 20`**,
   switches output to the **`yaml` callback** and enables **`profile_tasks`** so
   the slow tasks name themselves.
2. Check what is **really active** with `ansible-config dump --only-changed --type all`,
   and understand why your file only wins when the run starts from its
   directory.
3. Archive the proof: drop that dump on `db1.lab` as `/tmp/lab03a-config.txt`,
   owner `root`, mode `0644`.
4. Keep the capture honest: a command that only reads must never report
   `changed`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/ansible-config-fichier/
