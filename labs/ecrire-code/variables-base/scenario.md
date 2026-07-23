# Context — The default that got committed as production

The `db1.lab` playbook carries its values inside the file: service name, port,
database engine, connection limit. Last Friday someone edited that file to
point a run at production, ran it, and forgot to revert. The next colleague
pulled the repo and pushed production settings onto a test host. The values are
not the problem. Hardcoding them in one place, and **editing that place to
change a single run**, is.

You restructure it from **control-node.lab**.

Your mission:

1. Split the sources: keep the service identity in the play's **`vars:`**, move
   the database settings to an external file loaded by **`vars_files:`**.
2. Run it once with nothing on the command line, and confirm each variable
   resolves to the value coming from its own source.
3. Override two of them at run time with **`--extra-vars`**, without touching a
   single file.
4. Write the resolved values on `db1.lab` and read them back: only the two
   overridden ones moved. Then say which level wins, and why `vars_files:`
   (level 14) would beat the play's `vars:` (level 12) if both carried the same
   variable, and not the other way round.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/variables-base/
