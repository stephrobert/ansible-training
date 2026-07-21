# Challenge `lineinfile:`

## Brief

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

## Success criteria

- First run: `changed: 3` or more depending on the initial state.
- Second run: **`changed: 0`** (strict idempotence).
- `sshd -T | grep -E "PermitRootLogin|MaxAuthTries|AllowUsers"` returns the 3 expected lines.
- `sshd -t` returns **no** error.

## Hints

- For idempotence with `backrefs: true`, the regexp must match both
  the original line and the line after modification, use a group
  that captures the prefix (spaces + parameter name).
- `AllowUsers` may not exist at all, use a `lineinfile:` without
  `backrefs` for that task.
