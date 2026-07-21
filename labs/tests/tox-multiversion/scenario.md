# Context — A bug report from a version you never ran

An issue lands on your published role: it fails on `ansible-core` 2.16. You
cannot reproduce it, because your machine runs 2.18 and always has. Your users
do not. Some are pinned to the LTS by their platform team, others are already on
the newest release, and your single-version test suite has been blind to all of
them. Reproducing this by hand means rebuilding a virtualenv per version, and
nobody on the team will do that twice.

Your mission, from the project directory:

1. Declare an environment **per `ansible-core` version** to support, each one
   isolated and pinning its own version, so the versions can never leak into
   each other.
2. Have every environment run the full Molecule cycle against the same role, so
   "it passes" means the same thing on all of them.
3. Make the whole matrix runnable in a **single command**, and a single version
   targetable on demand when you are chasing one specific failure.
4. Read the outcome: a divergence between environments is a portability bug in
   the role, not a flaky test.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-tox-multiversion/
