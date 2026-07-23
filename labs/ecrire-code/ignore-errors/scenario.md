# Context — The keyword that hides your outages

Somebody sprinkled `ignore_errors: true` across the playbook until it stopped
being red. It is green now. It is also lying: a failed database migration
scrolls past as a discreet `...ignoring`, and the play ends in success. The
keyword is not evil, and it has a couple of honest uses — a cleanup that must
tolerate an already-absent service, for one. It is the reflex that is the
problem, and the only cure is to see precisely what it does and does not do.

You measure it on `db1.lab`, from **control-node.lab**.

Your mission:

1. Try to stop a service that does not exist on `db1.lab`: a guaranteed
   failure, and a legitimate one in a cleanup.
2. Ignore that error explicitly, putting the keyword where it belongs — it
   qualifies the task, it is not a module parameter.
3. Prove the play carried on: the next task runs, leaves its marker, and the
   recap reports `failed=0` even though a task failed.
4. Then argue against yourself: name what `failed_when` or `block`/`rescue`
   would have given you here that a silent ignore never will.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/ignore-errors/
