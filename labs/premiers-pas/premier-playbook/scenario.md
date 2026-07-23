# Context : A status page on db1, and SELinux says no

The monitoring team wants a small HTTP endpoint on **db1.lab**. Port 80 is off
the table on that host, so it has to be **8888**. Trivial, until the first
attempt: `nginx` refuses to start, the log says *"bind() to 0.0.0.0:8888 failed
(13: Permission denied)"*, and nothing in the config is wrong. Welcome to RHEL:
a non-standard port is not just a firewall matter, SELinux has an opinion too.

You write this from **control-node.lab**. Nobody logs into db1 to fix it by
hand.

Your mission:

1. Install **`nginx`** on `db1.lab`, started and enabled at boot.
2. Make it listen on **8888** instead of 80, and make **SELinux** accept that
   port instead of silently killing the service.
3. Open **8888** in firewalld so the rule applies immediately **and** survives
   a reboot.
4. Serve the exact welcome page the challenge asks for, then read the
   `PLAY RECAP` of a second run: it must be `changed=0`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premier-playbook/
