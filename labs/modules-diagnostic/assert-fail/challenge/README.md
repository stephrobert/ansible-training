# 🎯 Challenge — Defensive validation with `assert:` + `fail:`

## ✅ Objective

On **db1.lab**, write a play that **validates the prerequisites** before writing
a marker file `/tmp/lab-assert-validated.txt`. The validations must:

1. Check the OS (AlmaLinux/RedHat/Rocky **only**), `assert:`.
2. Check the major version ≥ 9, `assert:`.
3. Check that there is **at least** 512MB of RAM, `assert:`.
4. **Fail explicitly** via `fail:` if the inventory_hostname is not
   `db1.lab` (the play is designed only for db1).

## 🧩 Steps

1. **`assert:`** with 3 conditions and a clear `fail_msg:`.
2. **`fail:`** with `when:` on `inventory_hostname != 'db1.lab'`.
3. **`copy: content:`** to write `/tmp/lab-assert-validated.txt` after validation.

## 🧩 Skeleton

```yaml
---
- name: Challenge - assert + fail validation
  hosts: db1.lab
  become: true

  pre_tasks:
    - name: Refuser tout host autre que db1.lab
      ansible.builtin.fail:
        msg: ???
      when: ???

    - name: Valider OS + version + memoire
      ansible.builtin.assert:
        that:
          - ???
          - ???
          - ???
        fail_msg: ???
        success_msg: ???

  tasks:
    - name: Marker - validation OK
      ansible.builtin.copy:
        content: |
          Validations OK
          OS : {{ ansible_distribution }} {{ ansible_distribution_version }}
          Memoire : {{ ansible_memtotal_mb }} Mo
        dest: ???
        mode: "0644"
```

> 💡 **Traps**:
>
> - **`assert:`** = precondition. If false, the play stops (failed).
>   To warn without blocking: `assert:` + `ignore_errors: true` (but
>   not idiomatic, prefer a conditional `fail:`).
> - **`that:`** = list of conditions. **All** must be true.
>   Format: strings or lists. For OR: `or` Jinja in a string.
> - **`fail:` + `when:`**: alternative to `assert:`. More flexible if the
>   condition comes from a complex `register`.
> - **`success_msg`** vs **`fail_msg`**: custom message depending on the result.
>   Improves the log readability enormously.

## 🚀 Run

```bash
ansible-playbook labs/modules-diagnostic/assert-fail/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lab-assert-validated.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-diagnostic/assert-fail/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-assert-validated.txt state=absent"
```

## 💡 Going further

- **`pre_tasks:` vs `tasks:`**: the `pre_tasks:` run **before** any included
  role, useful to validate prerequisites before the roles import.
- **`quiet: true`**: silences the `assert:` that pass (useful on 50+ assertions).
- **`force_handlers: true`**: trigger the handlers even in case of an
  `assert: failed` (rare but useful to notify of a precondition failure).
- **`set_fact + assert` pattern**: compute a value, then assert it.
- **Lint**:

   ```bash
   ansible-lint labs/modules-diagnostic/assert-fail/challenge/solution.yml
   ```
