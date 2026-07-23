# 🎯 Challenge — Continue after an ignored error

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**:

1. Tries to **stop a nonexistent service**, the task fails.
2. **Ignores the error** explicitly.
3. Then writes `/tmp/ignore-after.txt` containing `play continued`, proof
   that the play continued despite the failure.

The play ends in success (`failed=0`) despite the silent error.

## 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-ignore-errors
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧩 Skeleton

```yaml
---
- name: Challenge - ignore_errors continue le play
  hosts: ???
  become: ???

  tasks:
    - name: Stopper un service qui n'existe pas
      ansible.builtin.systemd_service:
        name: ce-service-nexiste-pas
        state: stopped
      ignore_errors: ???

    - name: Marqueur post-échec ignoré
      ansible.builtin.copy:
        dest: ???                       # /tmp/ignore-after.txt
        content: ???                    # "play continued"
        mode: "0644"
```

> 💡 **Pitfalls**:
>
> - **`ignore_errors` ≠ `ignore_unreachable`**: the first ignores task
>   failures, the second unreachable hosts. In the exam, read
>   carefully which type of error the instructions ask you to ignore.
> - **`ignore_errors: true`** is a **task-level keyword**, not a
>   module parameter. Placing it inside `systemd_service:` gives an
>   "Unsupported parameters" error.
> - **Anti-pattern**: `ignore_errors: true` on a **critical** task
>   hides a real problem. Always combine it with `register:` + `when:`
>   to react instead of just ignoring.
> - **Reading the `PLAY RECAP`**: `failed=0, ignored=1`. The
>   `ignored` column does not exist in all versions, but the error
>   counter does not increment with `ignore_errors`.

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/ignore-errors/challenge/solution.yml
```

🔍 **Expected output**:

- 1st task: `failed!` but `...ignoring`
- 2nd task: `changed`
- `PLAY RECAP`: `failed=0, ignored=1`

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/ignore-errors/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-ignore-errors
```

## 💡 Going further

- **`ignore_unreachable: true`**: continues even if the host becomes
  unreachable (different from `ignore_errors`, which covers only **task
  failures**).
- **`ignore_errors` vs `failed_when: false`**: equivalent in practice to
  mark a failure as non-blocking. Prefer `failed_when: ...` if you
  want to condition.
- **Combine with `register:`**: capture the result to react later via
  `when: previous_task is failed`.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/ignore-errors/challenge/solution.yml
   ```
