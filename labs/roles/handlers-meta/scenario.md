# Context — nginx restarts on every run, and nobody knows what shipped

Two complaints landed the same morning. Ops: the deployment role restarts nginx
on **every** run, dropping connections even when nothing changed. Compliance: no
trace tells them what was deployed, where, and on which port. Both symptoms have
one root cause: the role does its reacting inside `tasks:` and documents nothing
about itself. Reactions belong in handlers, identity belongs in `meta/`.

Your mission, from **control-node.lab**:

1. Deploy the `webserver` role on **db1.lab** with a custom listening port of
   **8080**, and a custom index page carrying the target's hostname.
2. Make the change trigger the role's handlers: a service restart, a service
   reload, and a **non-service** handler that writes a deployment trace.
3. The deployment trace must record the host **and** the effective port, so the
   handler proves it read the overridden value and not the shipped default.
4. Confirm the role's `meta/main.yml` identity card is complete and readable.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/handlers-meta/
