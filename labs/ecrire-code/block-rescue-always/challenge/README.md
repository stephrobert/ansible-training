# 🎯 Challenge — `block` + `rescue` + `always` on a deliberate error

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Launches inside a `block:` a command that **fails deliberately**.
2. Catches the failure in `rescue:` which lays down `/tmp/challenge-rescue.txt` with the
   content `rescue triggered (block failed)`.
3. **Always** lays down `/tmp/challenge-always.txt` with `always executed` in
   `always:`.
4. The final `PLAY RECAP` must show **`failed=0`**: the rescue caught
   the error and the play ends in **success**.

## 🧩 Pattern

```yaml
- name: Bloc transactionnel
  block:
    - <tâche qui peut échouer>
  rescue:
    - <tâche exécutée si une tâche du block a échoué>
  always:
    - <tâche toujours exécutée, succès ou échec>
```

Python analogy: `try / except / finally`.

## 🧩 Skeleton

```yaml
---
- name: Challenge - block / rescue / always
  hosts: db1.lab
  become: true

  tasks:
    - name: Bloc avec rescue + always
      block:
        - name: Tâche qui échoue volontairement
          ansible.builtin.command: ???    # commande qui retourne rc != 0
          changed_when: false             # cmd qui ne modifie pas l'état réel

      rescue:
        - name: Marqueur rescue (capté)
          ansible.builtin.copy:
            dest: ???
            content: ???
            mode: "0644"

      always:
        - name: Marqueur always
          ansible.builtin.copy:
            dest: ???
            content: ???
            mode: "0644"
```

> 💡 **Hint for the failing command**: `/bin/false` always returns rc=1. You
> can also use `command: /bin/sh -c 'exit 1'`.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/block-rescue-always/challenge/solution.yml
```

🔍 **Expected output**:

- `TASK [Tâche qui échoue volontairement]` → `FAILED!`
- `TASK [Marqueur rescue]` → `changed`
- `TASK [Marqueur always]` → `changed`
- `PLAY RECAP`: `failed=0` (the rescue caught it)

> 💡 **Traps**:
>
> - **`block:` + `rescue:` + `always:`**: Ansible's try/except/finally
>   structure. `rescue` only runs if a task in the `block` fails.
>   `always` runs **always**, on success or failure.
> - **`ignore_errors:` in a `block`**: ignores the error AND does not trigger
>   the `rescue`. Use it sparingly: prefer `rescue`, which
>   is more explicit.
> - **`failed_when:` at the task level**: lets you **force** a
>   failure on a custom condition. Combined with `block`, it gives you
>   fine-grained control of the flow.
> - **Variables available in `rescue`**: `ansible_failed_task` and
>   `ansible_failed_result` for debugging. Do not confuse them with
>   `ansible_failed_handler` (failed handlers).

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/block-rescue-always/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-block-rescue-always
```

## 💡 Going further

- **`ansible_failed_task` / `ansible_failed_result`**: magic variables
  available in `rescue:` that expose the task that failed and its
  result. Useful for logging or notifying.
- **Nested blocks**: a `block:` can contain another `block:` with its
  own `rescue:`. A cascading fallback pattern.
- **Difference with `ignore_errors`** (lab 25): `ignore_errors` silently
  ignores the failure; `block/rescue` allows an explicit **catch
  action** (rollback, log, notification).
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/block-rescue-always/challenge/solution.yml
   ```
