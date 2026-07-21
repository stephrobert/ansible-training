# Context — One playbook, hosts that are not the same

The playbook has to run on the whole fleet, and the fleet is not homogeneous:
some hosts belong to the RedHat family and some do not, some run a version old
enough to lack the feature, and one option should only be on where the team
explicitly asked for it. Today there are three near-identical playbooks,
copy-pasted from one another. They diverged the day someone fixed a bug in
exactly one of them.

You collapse the logic into a single play on `db1.lab`, gated by conditions.

Your mission:

1. Gate a task on a **fact**: it applies to the RedHat family and skips
   everywhere else.
2. **Combine two conditions** for the version-specific task: the right
   distribution *and* a version high enough.
3. Handle a flag that may not exist at all: check it is **defined** before
   reading it, then coerce it — a flag passed on the command line is a string,
   not a boolean, and it is truthy either way.
4. Prove the skip is clean: the Debian task must be **skipped, not failed**,
   and its file must be nowhere on db1.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/conditions-when/
