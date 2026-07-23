# Context — The hub stopped accepting your role, and your users didn't notice

Your standalone role is published, used by teams you have never met, and the
platform you publish to now takes collections only. So the role has to move. The
constraint is that nobody downstream is going to edit their playbooks on your
schedule: they call your module by its old name, in code you do not own, and a
rename that breaks them is your problem, not theirs. You need the move to be
invisible today and obvious enough that they migrate eventually.

Your mission, from **control-node.lab**:

1. Move the role **and its custom module** into a collection under your namespace,
   putting each where the collection layout expects it.
2. Set up a **redirect** so a playbook calling the module by its **old name** keeps
   working, resolving to the new location without anyone editing anything.
3. Prove **both** names work against **db1.lab**: the new fully qualified name, and
   the legacy one going through the redirect.
4. Confirm the legacy path emits a **deprecation warning**. Compatibility that is
   silent is compatibility forever, and that is not what you signed up for.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/migration-role/
