# Context — The test suite that passes on a lie

Your Molecule scenario is green, and it proves almost nothing. The instance
starts bare, so the role installs its own prerequisites and the test never
exercises the real starting state. The run pulls no collections, so it passes
locally and explodes in CI. Nobody knows which task eats the four minutes. And
the cycle never re-runs the role, so a role that changes something on every pass
still reports success. A green suite that cannot fail is decoration.

Your mission, from the project directory:

1. Pre-condition the instance before the role runs, so the test starts from the
   state a real host would be in, and declare the Galaxy dependencies the
   scenario needs instead of relying on what happens to be installed.
2. Give each instance its own variables, so the scenario stops assuming every
   platform is identical.
3. Pin the cycle's step order explicitly, and make sure the **idempotence** step
   is part of it: the suite must be able to catch a role that never settles.
4. Turn on task timing, and name the slowest step.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-installation-config/
