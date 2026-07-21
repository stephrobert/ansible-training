# Context — Produce the evidence file the auditor is asking for

The auditor wants proof that the sensitive files on **db1.lab** carry the right
permissions, and "I looked, it's fine" is not proof. Three files are on the
list: the account database with a fingerprint that will let a later run detect
tampering, the shadow file whose owner must be root, and the sudo config, which
sudo itself ignores if its mode drifts from 0440. The report must be produced
from **control-node.lab**, replayable, and must **change nothing** on the audited
host.

Your mission:

1. Collect the state of the three files on **db1.lab** in **read only**: an
   audit that modifies its subject is not an audit.
2. Add a **SHA256 fingerprint** on the account database, since the module does
   not compute one by default and its default algorithm is not the one you want.
3. Gather what each file needs to prove: **mode** for all three, **owner** for
   the shadow file.
4. Assemble the whole thing into a readable **report** on the host, one entry
   per file.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/diagnostic/module-stat/
