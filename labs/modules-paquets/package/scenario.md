# Context — Standardize the toolbox, and get telnet off the server

Two things landed on your desk the same morning. The on-call team is tired of
finding **web1.lab** without an editor worth the name or shell completion, and
the security scan flagged the `telnet` client, whose cleartext protocol has no
business on a server in 2026. Same play, opposite directions: install what is
missing, remove what should not be there. And since the Debian fleet arrives
next quarter, the playbook must not hardcode the RHEL package manager.

Your mission:

1. From **control-node.lab**, bring **web1.lab** up to the standard toolbox
   (editor, shell completion, tree view) in a **single transaction**, not one
   task per package.
2. Remove **`telnet`**, and make sure the removal is proven against the package
   database, not against a command that happens to be missing.
3. Stay **distro-agnostic**: the same playbook must survive the arrival of
   Debian nodes without an `apt` rewrite.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-package/
