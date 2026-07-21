# Context — Stop the playbook before it breaks the wrong machine

The incident review was blunt. A playbook written for the RHEL family ran on a
host that was not one, failed halfway through, and left the system in a state
nobody could describe: half configured, half untouched. It had checked nothing
before starting. This one will not repeat the mistake. It is meant for
**db1.lab**, for a recent RHEL-family distribution, on a machine with enough
memory, and it must **refuse to run** anywhere else rather than fail in the
middle.

Your mission:

1. From **control-node.lab**, make the play **refuse any host other than
   db1.lab**, with a message stating why, checked **before** anything else runs.
2. **Validate the prerequisites** in one go: a distribution from the RHEL family,
   major version 9 or above, and at least 512 MB of RAM.
3. Make the failure **readable**: a custom message on failure, one on success,
   so the log says what happened instead of dumping a raw boolean.
4. Only **after** validation, drop the marker proving the host passed the gate.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-assert-fail/
