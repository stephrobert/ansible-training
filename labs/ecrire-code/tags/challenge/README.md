# 🎯 Challenge — Special tags `always` and `never`

You know how to use `tags: install`. The challenge adds two special tags:

- **`always`**: the task runs **even if** the learner launches with `--tags configuration`.
- **`never`**: the task **never** runs unless you explicitly run `--tags reset`.

## ✅ Objective

Write `solution.yml` that targets `db1.lab` and contains:

1. An **`always` marker** task tagged `always` that drops
   `/tmp/challenge-tag-always.txt`
2. A **`configuration` marker** task tagged `configuration` that drops
   `/tmp/challenge-tag-configuration.txt`
3. A **destructive `reset` marker** task tagged `[never, reset]` that drops
   `/tmp/challenge-tag-reset.txt` and **removes** `/tmp/challenge-tag-configuration.txt`
   and `/tmp/challenge-tag-always.txt`

## 🧩 Instructions

Skeleton to complete:

```yaml
---
- name: Lab 07 — démontrer always + never + configuration
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: Marqueur always
      ansible.builtin.copy:
        dest: ???
        content: "always\n"          # STABLE content, see the trap below
        mode: "0644"
      tags: ???

    - name: Marqueur configuration
      ansible.builtin.copy:
        dest: ???
        content: "configuration\n"
        mode: "0644"
      tags: ???

    - name: Marqueur reset destructif (multi-tags)
      block:
        - name: Poser le marqueur reset
          ansible.builtin.copy:
            dest: ???
            content: "reset\n"
            mode: "0644"

        - name: Supprimer les autres marqueurs
          ansible.builtin.file:
            path: "{{ item }}"
            state: ???               # absent
          loop: [???, ???]
      tags: [???, ???]               # never + reset
```

1. Create `challenge/solution.yml` from the skeleton.
2. Run with `--tags configuration`:

   ```bash
   ansible-playbook labs/ecrire-code/tags/challenge/solution.yml --tags configuration
   ```

   Expected:
   - `/tmp/challenge-tag-always.txt` exists (always)
   - `/tmp/challenge-tag-configuration.txt` exists (tagged configuration)
   - `/tmp/challenge-tag-reset.txt` does **not** exist (tagged `never`)

3. **Do not run** the `--tags reset` command (it is destructive and would
   make the tests fail). The test verifies that reset did not run.

> 💡 **Pitfalls**:
>
> - **`always`** runs **even with `--tags X`** (where X ≠ always).
>   To skip it: `--skip-tags always`.
> - **`never`** runs **only** if requested explicitly with
>   `--tags <its_tag>`. Without `--tags`, it is skipped.
> - **Multi-tags**: `tags: [a, b]` lets the task match `--tags a`
>   OR `--tags b`. To match both, you would need `--tags a,b`.
> - **The conftest** runs the replay with `--tags configuration` (see
>   `_EXTRA_ARGS`). If you add other tags, remember to update it.
> - **Drop the markers with `copy:` and stable content**, not with
>   `file: state: touch` nor `shell: touch`. Those two report `changed` on
>   **every** pass (touch writes a new modification date, that is
>   its whole purpose), and `test_solution_idempotente` requires `changed=0` on the
>   second run. If you insist on `touch`, you must neutralize it with
>   `modification_time: preserve` and `access_time: preserve`.
> - **No `{{ ansible_date_time.iso8601 }}` in the `content:`**: the
>   content would change on every run and break idempotence, while proving
>   nothing more. What proves that a task ran under a given tag filter
>   is that its marker **exists**. The play also runs with
>   `gather_facts: false`: that fact is not even collected.

## 🧪 Validation

The `tests/test_tags.py` script checks on **db1.lab**:

- `/tmp/challenge-tag-always.txt` exists (proof of `always`)
- `/tmp/challenge-tag-configuration.txt` exists (proof of `--tags configuration`)
- `/tmp/challenge-tag-reset.txt` does **NOT** exist (proof `never` was not triggered)
- The **second pass** of the playbook changes nothing (`changed=0`)

```bash
pytest -v labs/ecrire-code/tags/challenge/tests/
```

## 🚀 Going further

- Redo the challenge running **without `--tags`**: `always` runs,
  `configuration` too, `never` still skipped.
- Run with **`--tags reset`**: `always` runs, `reset` too, and the
  configuration/always files are removed. Then check with an
  `ls /tmp/challenge-tag-*.txt`.

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean ecrire-code-tags
```

This target uninstalls/removes what the solution placed on the managed
nodes (packages, files, services, firewall rules) so you can
rerun the solution from scratch.
