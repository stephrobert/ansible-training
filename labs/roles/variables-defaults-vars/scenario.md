# Context — One role, two teams, two ports

The `webserver` role works fine, but it hardcodes port 80. The database team now
wants the same role on **db1.lab** listening on **8080**, because 80 is already
taken by a monitoring agent. A colleague's first reflex was to edit the role's
tasks; you refuse. A role that must be edited to be reused is not a role, it is
a copy waiting to happen. The knobs belong to the caller, the internals do not.

Your mission, from **control-node.lab**:

1. Deploy the `webserver` role on **db1.lab** while **overriding** its listening
   port to **8080** and its worker connections to **2048**, from the playbook
   only, without touching the role.
2. Inject a custom index page that carries the target's own hostname.
3. Prove the override landed: the open firewalld port and the rendered
   configuration must reflect **8080**, not the shipped default.
4. Establish which variables are meant to be overridable and which are internal
   details the caller must never reach.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/variables-defaults-vars/
