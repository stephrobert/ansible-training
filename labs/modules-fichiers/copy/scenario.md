# Context — Roll out the legal login banner on the web tier

The security audit closed on one blocking finding: **web1.lab** opens SSH
sessions with no legal notice, while compliance demands proof that access is
announced as monitored before the shell even appears. The same audit asks that
every host identify itself in its message of the day. You work from
**control-node.lab**: nothing gets typed by hand on the server, the banner
ships as a playbook so the next twenty servers cost one `--limit`.

Your mission:

1. Push the legal banner text from the control node to
   **`/etc/ssh/banner-rhce`** on **web1.lab**, owned by root, world-readable,
   with a **backup** of any previous version.
2. Write the server identity marker straight into **`/etc/motd-rhce`** as
   **inline content**, without shipping a source file for three words.
3. Keep both tasks **idempotent**: a second run must report zero changes.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-copy/
