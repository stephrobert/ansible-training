# Context — An identifier nobody should have to type

The support tool correlates incidents by a system identifier: short hostname,
then running kernel. Today someone builds that string by hand and pastes it
into the ticket, and gets it wrong roughly one time in five — usually right
after a kernel update, when the machine no longer runs what the ticket claims.
The host knows both halves perfectly well. You only have to ask it, assemble
the answer, and write it down.

You do it on **db1.lab** from **control-node.lab**, without gathering the full
fact set.

Your mission:

1. Capture the **short hostname** and the **running kernel** with two read-only
   commands, keeping each result.
2. Make sure those reads never report `changed`: a command that only looks at
   the system changes nothing, and must say so, or your playbook is never
   idempotent again.
3. Assemble the two captured values into a single **runtime fact**.
4. Write it on db1 as `system_id=<hostname>:<kernel>`, and know where a
   `set_fact` sits in the precedence order — and what `cacheable` changes.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/register-set-fact/
