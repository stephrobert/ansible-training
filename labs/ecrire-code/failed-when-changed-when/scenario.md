# Context — The command that reports "nothing found" with rc=1

Half the tooling on **db1.lab** ignores the convention. `grep` returns 1 when
it finds nothing. `diff` returns 1 when two files differ. The compliance
checker returns 1 to mean *"I changed something"*. Ansible reads any non-zero
return code as a failure, full stop, so the play aborts on a task that did
exactly what it was asked. Meanwhile a read-only `command:` proudly reports
`changed` on every single run, and your idempotence proof is worth nothing.

You teach Ansible the real semantics, from **control-node.lab**.

Your mission:

1. Run a command on `db1.lab` that exits with **rc=1**, and capture its result.
2. Redefine what **failure** means for that task: 0 and 1 are legitimate
   outcomes, anything above is a real error.
3. Redefine what **change** means: rc=1 is the signal that something actually
   moved, so the task must report `changed`, not `ok`.
4. Prove the play survived: the following task runs and the recap shows
   `failed=0`. Then work out which of the two conditions Ansible evaluates
   first, and why it matters.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/failed-when-changed-when/
