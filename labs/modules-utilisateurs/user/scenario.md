# Context — Onboard the new team onto the database server

Two people join the project Monday and the deployment pipeline needs its own
identity on **db1.lab**: Alice takes the admin role and must reach sudo, Bob
works as a developer, and a service account runs the deployments from an
application directory rather than a classic home. The NFS share the team will
mount reads permissions **by UID**, so the technical accounts must carry the
same numbers on every host. You provision this from **control-node.lab**.

Your mission:

1. Create the **team group** on **db1.lab** first, then the three accounts that
   depend on it: order is not negotiable.
2. Give Alice her admin privileges through the **secondary group** that grants
   sudo, **without stripping** the groups she may already belong to.
3. Pin the **fixed UIDs** on the two technical accounts, and give the deployment
   account its home under the application directory rather than `/home`.
4. Verify the whole thing is **idempotent**: a compliant account must report
   `ok`, never `changed`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-user/
