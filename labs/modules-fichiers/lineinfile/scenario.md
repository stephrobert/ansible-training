# Context — Harden the SSH daemon on the database server

Fail2ban reports a steady stream of root login attempts on **db1.lab**, the
server that holds production data. Security wants three things closed today:
no root over SSH, a strict cap on authentication retries, and an explicit list
of who may connect. The catch is that a typo in `sshd_config` plus a service
restart locks everyone out of a box you reach only through SSH. So you work
from **control-node.lab**, and the daemon never restarts on an invalid file.

Your mission:

1. Disable root SSH login on **db1.lab**, cut **`MaxAuthTries` to 3** while
   keeping the existing indentation of the line, and add **`AllowUsers ansible`**
   if it is missing.
2. **Validate the file before every write**: a config that `sshd` rejects must
   never reach the disk.
3. Restart the daemon **only once, at the end, and only if** something actually
   changed.
4. Guarantee strict **idempotence**: the second run must report `changed: 0`.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-lineinfile/
