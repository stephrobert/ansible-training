# Context — Open the web stack without leaving the door open at reboot

The application goes live on **web1.lab** tonight: the public site on HTTP and
HTTPS, plus two ports the dev team still needs for its staging instance. The
previous rollout is exactly why nobody trusts hand-typed firewall commands
anymore. The rules were applied at the console, worked all afternoon, and
vanished on the maintenance reboot: the site was unreachable at 6 a.m. and
nobody understood why. You rebuild the whole thing from **control-node.lab**.

Your mission:

1. Make sure firewalld is **installed, running and enabled at boot** on
   **web1.lab**, before writing any rule into thin air.
2. Allow the two **predefined web services** in the public zone, using their
   service names rather than raw port numbers.
3. Open the two **custom staging ports** in the same zone.
4. Every rule must be **active right now and survive the reboot**: getting only
   one of the two is precisely the trap that took the site down.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-firewalld/
