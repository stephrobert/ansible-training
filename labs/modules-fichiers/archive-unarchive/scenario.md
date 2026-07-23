# Context — Prove the backup and restore chain actually works

**db1.lab** carries a data directory that has never been backed up, and the
disaster recovery plan says the restore procedure is "documented". Nobody has
ever run it. Your manager wants the full chain demonstrated end to end before
the audit: produce an archive, restore it elsewhere, and show both sides match.
The whole thing has to run from **control-node.lab** as a playbook a cron job
could replay every night without churning the disk.

Your mission:

1. Set up the source data on **db1.lab** under `/opt/data-source/`, then
   produce the compressed archive **`/opt/backup/data.tar.gz`** from it.
2. Restore that archive into **`/opt/restored/`**, remembering the archive
   lives **on the managed node**, not on your control node.
3. Make the extraction **idempotent**: the second run must **skip** the restore
   instead of rewriting the files and churning every mtime.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/archive-unarchive/
