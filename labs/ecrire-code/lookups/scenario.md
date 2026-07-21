# Context — The token lives here, the server needs it there

The API token sits in a file on the control node. **db1.lab** has never seen
it, and should never hold a copy of it beyond the config file you are about to
render. A colleague suggested copying the token onto db1 first and reading it
from there, which defeats the entire point of keeping it on one machine.
Ansible can read local data at template time and push only the result. That is
what lookups are for, and the direction is the whole lesson.

You work from **control-node.lab**.

Your mission:

1. Read the **API token from a file on the control node** and push it into
   `/tmp/lookups-challenge.txt` on `db1.lab`.
2. Add a value taken from the control node's **environment**, and one taken
   from the **output of a command** run locally.
3. Convince yourself of the direction: all three values describe your control
   node, not db1 — even though the file lands on db1.
4. Note that a file lookup resolves **relative to the playbook**, not to your
   shell, and know when `query` should replace `lookup`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/lookups/
