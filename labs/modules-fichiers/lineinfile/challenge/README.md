# Harden the SSH daemon on the database server

## The situation

Fail2ban reports a steady stream of root login attempts on **db1.lab**, the
server that holds production data. Security wants three things closed today:
no root over SSH, a strict cap on authentication retries, and an explicit list
of who may connect. The catch is that a typo in `sshd_config` plus a service
restart locks everyone out of a box you reach only through SSH. So you work
from **control-node.lab**, and the daemon never restarts on an invalid file.

Your mission:

1. Disable root SSH login on **db1.lab**, cut **`MaxAuthTries` to 3** while
   keeping the existing indentation of the line, and add **`AllowUsers ansible`**
   if it is missing.
2. **Validate the file before every write**: a config that `sshd` rejects must
   never reach the disk.
3. Restart the daemon **only once, at the end, and only if** something actually
   changed.
4. Guarantee strict **idempotence**: the second run must report `changed: 0`.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-lineinfile/ (in French)

## Challenge `lineinfile:`

### Brief

On **db1.lab**, write a **`solution.yml`** playbook that:

1. **Disables** SSH root login (`PermitRootLogin no`).
2. Reduces **MaxAuthTries** to `3` (keeping the existing indentation via `backrefs`).
3. Adds the line **`AllowUsers ansible`** if absent.
4. **Validates** each change with `sshd -t -f %s` before writing.
5. Notifies a **handler** `Restart sshd` that triggers only at the end if
   at least one of the 3 tasks is `changed`.

> 🎯 **No skeleton here, on purpose.** By this point you have written enough
> playbooks to start from a blank file, and that is exactly what the EX294
> asks: the exam hands you no canvas. The hints below target the traps of
> this module, not the YAML syntax.

### Success criteria

- First run: `changed: 3` or more depending on the initial state.
- Second run: **`changed: 0`** (strict idempotence).
- `sshd -T | grep -E "PermitRootLogin|MaxAuthTries|AllowUsers"` returns the 3 expected lines.
- `sshd -t` returns **no** error.

### 🧩 Stuck?

```bash
dsoxlab hint modules-fichiers-lineinfile
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.
