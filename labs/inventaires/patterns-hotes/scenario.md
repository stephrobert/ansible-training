# Context — Target the right hosts without editing the playbook every time

The same playbook has to run on a different perimeter every time: only the web
servers under test, the web tier except the one host being investigated, the
whole fleet except staging. The current habit is to edit the `hosts:` line
before each run, and the accident everyone saw coming happened last week: a
leftover perimeter, and the play went out on every server. The playbook must
stop knowing who it targets. That decision belongs at **run time**, from
**control-node.lab**.

Your mission:

1. Write a play targeting **all hosts**, dropping a marker named after each
   host: no perimeter hardcoded in the YAML.
2. Get the filtering done at **run time**, so the same file serves the three
   perimeters without a single edit.
3. Hit exactly three targets: the **intersection** of the web tier and staging,
   the web tier **minus** one specific host, and the whole fleet **excluding**
   staging.
4. Prove the aim: only the expected hosts carry the marker, and the others were
   never touched.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/patterns-hotes/
