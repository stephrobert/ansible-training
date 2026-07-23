# Context — Apply the kernel hardening baseline to the database server

The security baseline lands on **db1.lab** with four kernel settings to sort
out. The box must route traffic for the backend subnet, survive a SYN flood,
stop exposing kernel pointers through `/proc` to any local user, and quit
swapping out a database that has plenty of RAM. Two constraints frame the job.
The settings must be **live now**, because rebooting a production database to
apply a parameter is not an option, and they must **survive the reboot** anyway.

Your mission:

1. From **control-node.lab**, set the four baseline parameters on **db1.lab**:
   IPv4 forwarding, SYN cookies, kernel pointer restriction, and swap
   reluctance.
2. Write them all into a **dedicated file under `/etc/sysctl.d/`**, not into the
   deprecated global config: a role owns its file and stays versionable.
3. Have them **applied immediately**, without waiting for a reboot.
4. Drive the four parameters from a **single task**, and confirm the second run
   reports no change.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-sysctl/
