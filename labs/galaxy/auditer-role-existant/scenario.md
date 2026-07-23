# Context — A stranger's code, running as root, on your production

A developer wants a Galaxy role added to the project by Friday. It has plenty of
stars, so the discussion is treated as settled. It is not. That role is arbitrary
code that will run with **`become: true`** on every production server you own,
and nobody in the room has opened it. Stars measure popularity, not whether the
thing downloads a binary over plain HTTP or has been abandoned since 2021.

Your mission, from the project directory:

1. Turn the vague feeling of "it looks fine" into a **scored checklist**, over
   six axes: maintainer health, code quality, security, tests, compatibility and
   idempotence.
2. Read the role's own declared identity to find which platforms it actually
   claims to support, and confront that with the fleet you run.
3. Hunt the classic tells: hardcoded secrets, unencrypted downloads, short module
   names, arbitrary commands with nothing to make them idempotent.
4. Turn the score into a **decision** you can defend: adopt, fork, or refuse.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/auditer-role-existant/
