# Context — Harden the app config without touching the neighbours

The application on **db1.lab** reads `/etc/myapp.conf`, and three changes
landed at once: the API moved to a new domain behind TLS, the service port
switched to 8443, and SSL must be turned on. The trap is written into the
file itself: it stacks a `[server]` and a `[client]` section, and both
declare `ssl_enabled=false`. Only the server side must flip to `true`; a
blind substitution would also flip the client and break its handshake. You
operate from **control-node.lab**, on a file that must come out surgically
edited.

Your mission:

1. Move the API URL to **https on its new domain**, everywhere it appears,
   keeping the path intact.
2. Bump the **port to 8443** while preserving the `port=` prefix, rather
   than rewriting the whole line.
3. Enable SSL **in the `[server]` section only**, by **bounding the
   substitution zone** rather than trusting the pattern.
4. Prove the collateral damage is nil: `[client]` still says
   `ssl_enabled=false`, and a second run reports no change.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-replace/
