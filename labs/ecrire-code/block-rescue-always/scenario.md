# Context — The migration died halfway and left the door open

A migration on **db1.lab** failed in the middle last month. It had already put
the service into maintenance mode, and it never took it back out: the failure
aborted the playbook on the spot, and the cleanup step, sitting neatly at the
bottom of the file, never ran. The host stayed out of rotation until someone
noticed. An error is not the problem: an error with no recovery and no cleanup
is. You rebuild the play from **control-node.lab**, with a real transaction
around it.

Your mission:

1. Group the risky tasks in a **`block:`** on `db1.lab`, including one that is
   certain to fail.
2. Catch that failure in a **`rescue:`** that records what happened, instead of
   letting the play die where it stands.
3. Guarantee the cleanup runs in **`always:`**, whether the block succeeded or
   blew up.
4. Read the recap: **`failed=0`**. The error happened, it was handled, the play
   is a success. Then find the variable that tells `rescue` what actually
   failed.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/block-rescue-always/
