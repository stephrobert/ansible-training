# Context — Three accounts requested, one already revoked

HR sent the list: three accounts to create on **db1.lab**, each with its own
shell. Between the request and today, one of them was revoked — the person
never joined. The list still carries all three, with a flag saying which are
active, because that list is the source of truth and nobody is allowed to trim
it by hand. Your playbook must read the flag, not the length.

You write it from **control-node.lab**.

Your mission:

1. Iterate over the account list and create **only the ones flagged active**,
   each with the shell it asks for.
2. Make sure the revoked account **does not exist** on the host, even if an
   earlier run created it before the revocation.
3. Keep the console readable: forty accounts printed as raw dicts is a wall of
   noise — **label** each iteration by its name.
4. Write a recap file listing the active accounts, alphabetical and
   comma-separated, derived from that same list rather than retyped.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-loop/
