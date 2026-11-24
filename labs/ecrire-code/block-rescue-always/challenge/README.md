# The migration died halfway and left the door open

## The situation

A migration on **db1.lab** failed in the middle last month. It had already put
the service into maintenance mode, and it never took it back out: the failure
aborted the playbook on the spot, and the cleanup step, sitting neatly at the
bottom of the file, never ran. The host stayed out of rotation until someone
noticed. An error is not the problem: an error with no recovery and no cleanup
is. You rebuild the play from **control-node.lab**, with a real transaction
around it.

Your mission:

1. Group the risky tasks in a **`block:`** on `db1.lab`, including one that is
   certain to fail.
2. Catch that failure in a **`rescue:`** that records what happened, instead of
   letting the play die where it stands.
3. Guarantee the cleanup runs in **`always:`**, whether the block succeeded or
   blew up.
4. Read the recap: **`failed=0`**. The error happened, it was handled, the play
   is a success. Then find the variable that tells `rescue` what actually
   failed.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/block-rescue-always/ (in French)

## 🎯 Challenge — `block` + `rescue` + `always` on a deliberate error

### ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Launches inside a `block:` a command that **fails deliberately**.
2. Catches the failure in `rescue:` which lays down `/tmp/challenge-rescue.txt` with the
   content `rescue triggered (block failed)`.
3. **Always** lays down `/tmp/challenge-always.txt` with `always executed` in
   `always:`.
4. The final `PLAY RECAP` must show **`failed=0`**: the rescue caught
   the error and the play ends in **success**.

### 🧩 Pattern

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

### 🧩 Skeleton

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

### 🚀 Launch

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

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/block-rescue-always/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-block-rescue-always
```

### 💡 Going further

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
