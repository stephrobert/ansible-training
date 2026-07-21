# Context : nginx is telling the world its version number

The pentest report came back with two findings that cost nothing to fix and
have been open for a year: **db1.lab** answers every HTTP request with its exact
nginx version in the `Server` header, and signs its error pages with the same
details. Free reconnaissance for anyone scanning the range. Second finding:
responses carry no `X-Content-Type-Options` header, leaving browsers free to
sniff the type of whatever is served. Changing the config is two lines. Getting
it **live** without restarting nginx on every playbook run, and leaving an audit
trail, is the real work.

You operate from **control-node.lab**.

Your mission:

1. On `db1.lab`, harden the `nginx` config so it stops advertising its version,
   then make it refuse MIME sniffing.
2. Have the hardening task **notify two handlers**: the reload, and a
   timestamped entry in a local journal file the auditors can read.
3. Prefer a **reload** over a restart, and force the handlers to run inside the
   same play so you can verify the effect immediately.
4. Prove it from the outside: the `Server` header must read exactly `nginx`,
   version gone, the response must carry `X-Content-Type-Options: nosniff`,
   and a second run must notify nothing at all.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/handlers/
