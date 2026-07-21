# Context — One file you own, one file you are only visiting

Two incidents in the same week, opposite causes. First: a `lineinfile` written
without a `regexp` appended its entry to `/etc/hosts` on every single run —
forty identical lines by the time anyone looked. Second: a colleague decided to
manage `/etc/hosts` with a template instead, took ownership of the entire file,
and wiped the entries another tool had legitimately put there. Neither module
is wrong. They answer different questions.

You put them side by side on `db1.lab`, from **control-node.lab**.

Your mission:

1. Add a **single host entry** to `/etc/hosts` without disturbing the lines
   already there.
2. Make that addition idempotent by **matching** the line instead of appending
   blindly: the missing `regexp` is the entire first incident.
3. Generate `/etc/myapp.conf` **entirely from a template**, every value
   interpolated from structured variables.
4. Then state the rule out loud: which of the two files you own, which one you
   are only visiting, and why that answer, not taste, picks the module.

The full method is in the companion guide:
https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/lineinfile-vs-template/
