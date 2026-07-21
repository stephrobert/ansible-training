# Context — Overwrite the config, lose the evidence

The banner on **db1.lab** is generated from a template now, which is progress.
What is not progress: last week's run replaced it with a broken version, and
nobody could produce the previous one. It existed in exactly one place, the
file that had just been overwritten. On a banner, that costs an apology. On the
config of a service that will not restart, at 6 p.m. on a Friday, it costs the
evening.

You make the generation safe, from **control-node.lab**.

Your mission:

1. Render `/etc/banner.txt` on `db1.lab` from a **Jinja2 template**, the header
   text coming from a variable rather than a literal.
2. Build the metadata block by **iterating over a dict**, so that adding a
   field later means editing data, not the template.
3. Keep the previous version: every overwrite must leave a **timestamped
   backup** behind.
4. Set permissions explicitly and **quote the mode** — an unquoted octal is not
   the mode you think it is. Then find out what `validate:` would buy you on a
   real config.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/module-template/
