# Context — One deployment record, not one per host

Every rollout on **web1.lab** and **web2.lab** leaves a local trace on each
node, and that part works. The central record does not: the team wants **one**
line on **db1.lab** stating that the rollout happened. Today the playbook
writes it once per webserver, so db1 receives the same file twice in the same
second. On a forty-node fleet it would be forty times. And db1 is not even in
the `webservers` group.

You fix it from **control-node.lab**, without adding a second playbook.

Your mission:

1. From a play targeting `webservers`, drop a **local marker** on each host,
   named after the host itself.
2. Write the **central record on `db1.lab`** from that same play, even though
   db1 belongs to another group entirely.
3. Make sure that record is written **exactly once** for the whole batch, not
   once per webserver.
4. Read the `web1.lab -> db1.lab` notation in the output, then check the
   isolation: the central record exists on db1 and on neither webserver.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/delegation/
