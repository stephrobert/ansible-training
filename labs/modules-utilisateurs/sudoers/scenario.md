# Context — Rebuild sudo rights after the "everyone is root" era

The audit of **db1.lab** found what happens when sudo grows organically: a
handful of people effectively hold full root, passwordless, and nobody
remembers granting it. Three legitimate needs remain, and only three. Alice
administers the box, but must retype her password so a stolen open terminal is
not a free root shell. The ops team automates and cannot stop on a prompt. And
Alice must be able to run the deployment script **as the service account**,
without becoming root for it. One typo in a sudo file locks the whole team out,
so nothing gets written unvalidated.

Your mission:

1. From **control-node.lab**, set up the prerequisites on **db1.lab**: the
   accounts, the ops group, and its membership.
2. Grant Alice **full sudo with a password required**, and the ops group **full
   sudo without a password**: mind the module's default here, it does not lean
   the way you would hope.
3. Let Alice run **only the deployment script**, and **as the deploy account**,
   not as root.
4. Land each rule in its **own file under `/etc/sudoers.d/`**, syntax-validated
   before it ever reaches the disk.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/utilisateurs/module-sudoers/
