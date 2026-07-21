# Context — Retire the curl calls hiding in the provisioning playbook

The playbook that provisions **db1.lab** still downloads its reference files
with `command: curl`, and it shows. Every run reports `changed`, because a shell
command has no idea whether the file is already there, and the pipeline can no
longer tell a real change from background noise. Nothing checks what actually
lands on disk either: whatever the mirror serves gets written, corrupted or not.
One of the two files must never be overwritten once in place: it is the
reference the team amends locally, and a fresh download silently wipes those
edits. That one no longer sits in the open: the internal repository now serves
it from a protected area. You clean this up from **control-node.lab**, with no
shell command left.

Your mission:

1. Download the two reference documents onto **db1.lab** into `/opt/`, mode
   `0644`, using the **dedicated Ansible module**: no `curl`, no `wget`.
2. **Check the integrity** of the public document against the **sha256 checksum
   file the repository publishes next to it**, rather than trusting the bytes
   that arrive. Do not freeze a fingerprint into the playbook.
3. **Authenticate** the request for the second document, which the repository
   serves from a protected area.
4. Protect that second file so that **an existing copy is never re-downloaded**,
   whatever upstream now serves.
5. Prove the **idempotence**: a second run downloads nothing and reports no
   change.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/reseau/module-get-url/
