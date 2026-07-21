# Context — "I changed the value and nothing happened"

Two hours lost yesterday. A colleague set the value in the vars file, ran the
playbook against **db1.lab**, and got the old one. Set it again, in another
file: same result. They ended up editing the play itself, which is precisely
what nobody wants in the repo. Ansible resolves one variable name across
**twenty-two levels**, and there is nothing mysterious about it: you either
know the order or you spend your afternoons fighting it. You settle the
question experimentally, from **control-node.lab**.

Your mission:

1. Declare the **same variable** in the play's `vars:` and in a file loaded by
   `vars_files:`.
2. Run it bare and record the resolved value on db1: discover that
   `vars_files:` (level 14) **wins** against the play's `vars:` (level 12), the
   exact opposite of intuition.
3. Override both from the command line with **`--extra-vars`** and watch the
   top level win over everything else.
4. Explain the result instead of memorising it: say what each level is for, and
   why `--extra-vars` is the right tool for a one-off override and the wrong one
   for a permanent setting.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/
