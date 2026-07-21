# Context — Yellow on every run, and nobody reads the recap any more

The nightly play reports `changed=14` every single night, on hosts where nothing
has changed for weeks. The tasks are lying about their state: they redo the work,
they flush caches, and they have trained the team to ignore the recap entirely.
Which is exactly why last Tuesday's real change went unnoticed for three days. On
top of that the play takes eleven minutes, and management has started asking why.

Your mission, from **control-node.lab**:

1. Refactor the three offending operations on **db1.lab** so the play reports
   **`changed=0` on its second pass**: a raw command that must not re-run, a
   config line that must be matched rather than appended, and a read-only lookup
   that has no business reporting a change at all.
2. Prove the fix the only way that counts: run it twice and read the recap.
3. Measure a **baseline** before optimising: name the tasks that actually cost the
   eleven minutes rather than optimising by folklore.
4. Then tune the connection layer: fewer round trips per task, more hosts in
   flight, and a reused SSH connection. Re-measure and state the real gain.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/
