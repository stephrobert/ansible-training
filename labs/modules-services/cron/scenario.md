# Context — Schedule the backup and the cleanup that never ran

The `/tmp` partition on **db1.lab** filled up on Sunday and took the database
down with it, while the hourly backup everyone assumed was running turned out
to live in nobody's crontab. Both jobs must be scheduled, and above all
**auditable**: the previous admin edited a shared crontab by hand, and no one
can tell today who added what. You are switching to a dedicated, versioned file
deployed from **control-node.lab**, and failures must reach a human.

Your mission:

1. Provision a **file of your own under `/etc/cron.d/`** on **db1.lab**, rather
   than patching the shared crontab, so a role owns its schedule.
2. Set the **notification address** at the top of that file, so a failing job
   mails someone instead of dying in silence.
3. Schedule the two jobs as root: the **hourly backup** and the **daily 3 a.m.
   cleanup** of files older than a week in `/tmp`.
4. Guarantee **idempotence**: replaying the playbook must not stack a second
   copy of each job.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-cron/
