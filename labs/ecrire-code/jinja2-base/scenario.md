# Context — A login banner that lies about the machine

Every host greets you with a banner someone typed by hand years ago. Half of
them still advertise a service that was decommissioned two reorganisations
ago, one welcomes you to a hostname that no longer exists, and they are all
peppered with stray blank lines left by a previous attempt at generating them.
Ops wants one banner: generated, correct on every host, and readable.

You start with **db1.lab**, from **control-node.lab**.

Your mission:

1. Render `/etc/motd-challenge` from a **Jinja2 template**, the host naming
   itself from the inventory instead of from a literal string.
2. Show the role line **only when** the host actually carries that role: a
   conditional inside the template, not two templates side by side.
3. List the host's services with a **loop** driven by a variable, one per line.
4. Kill the stray blank lines with **whitespace control**: that is the whole
   difference between a generated banner and a banner that looks generated.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/jinja2-base/
