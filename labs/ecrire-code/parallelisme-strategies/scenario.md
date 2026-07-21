# Context — Both webservers went down in the same second

The last deployment took the site offline for ninety seconds. Nothing failed:
the playbook simply did its job on **web1.lab** and **web2.lab** in parallel
and restarted both at once. Behind a load balancer, two healthy nodes updated
simultaneously means zero nodes serving. The answer is not to slow everything
down, it is to tell Ansible to walk the fleet one host at a time and to stop
dead on the first failure rather than break the second node too. You fix it
from **control-node.lab**.

Your mission:

1. Target the `webservers` group and roll the play out **one host at a time**.
2. Set the tolerance to zero: the first failing host stops the play before it
   ever touches the next one.
3. Drop a **marker** on each host, and slow each batch just enough that the two
   modification times cannot collide. Keep the marker's contents stable across
   runs: its mtime is the witness, not what is written inside it.
4. Prove the sequencing instead of assuming it: web1's marker must be strictly
   older than web2's. Read the output too, the `PLAY` banner now appears once
   per batch, not once per run.
5. Replay the playbook with nothing changed: it must report no change at all.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/parallelisme-strategies/
