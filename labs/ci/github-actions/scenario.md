# Context — The role is open source now, and strangers will send patches

Your `webserver` role is public. The first outside pull request arrives tomorrow,
and you will not run it by hand: you neither trust the code nor have the time,
and nobody wants to be the human who forgot to test one distribution. Worse, a
workflow that clones the repo and runs untrusted code with a writable token is
how a role becomes an attack path. The gate has to be automatic, and it has to
be safe on a contributor's branch.

Your mission, from the project directory:

1. Have every push and pull request go through **two gates**: linting first, then
   the Molecule cycle, so a style failure never burns matrix minutes.
2. Spread the test job across a matrix of **distributions crossed with
   `ansible-core` versions**, running in parallel.
3. Cache the Python dependency install between runs, so the pipeline stays fast
   enough that people actually wait for it.
4. Lock the workflow down: **least-privilege token permissions**, and no
   credentials left behind in the checkout for later steps to reuse.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/ci-github-actions/
