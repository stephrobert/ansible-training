# 🎯 Challenge — Fixing a missing variable with the debugger

## ✅ Objective

Write a playbook that **fails on purpose** on an undefined `target_dir` variable, then use the **Ansible debugger** to **inject the variable at runtime** (`task_vars['target_dir'] = '/tmp'`) and make the task pass **without modifying the YAML**.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab90-debug.txt` |
| Permissions | `0644`, owner `root` |
| Content | "Debugger fix au runtime — lab 90 OK" |
| Mechanism | `debugger: on_failed` enabled on the copy task |

> ⚠️ **Interactive mode**: this challenge requires an interactive terminal.
> For the **pytest validation**, the final `solution.yml` must have
> `target_dir` correctly defined in `vars:` (not the broken version
> with the debugger: pytest runs after your fix).

## 🧩 Hints

### Step 1 — `solution.yml` skeleton

```yaml
---
- name: Challenge 90 — debugger fix runtime
  hosts: ???
  become: ???
  gather_facts: false
  vars:
    target_dir: ???                 # ← after your debug, set it here to /tmp

  tasks:
    - name: Déposer la preuve
      ansible.builtin.copy:
        dest: "{{ target_dir }}/lab90-debug.txt"
        content: "???"
        mode: ???
```

### Step 2 — Recommended workflow

1. **Phase 1 (interactive debug)**: start **without** `vars: { target_dir: /tmp }`,
   enable `debugger: on_failed`, observe the failure, inject at runtime via
   `task_vars['target_dir'] = '/tmp'` + `update_task` + `redo`.

2. **Phase 2 (permanent fix)**: once the cause is understood, **edit the YAML**
   to define `vars: { target_dir: /tmp }` cleanly and **remove**
   `debugger: on_failed` (which has no place in production code).

### Step 3 — REPL commands

| Command | Effect |
| --- | --- |
| `p task_vars['target_dir']` | inspect (should say `undefined`) |
| `task_vars['target_dir'] = '/tmp'` | injects the variable |
| `update_task` or `u` | recreates the task with the new vars |
| `redo` or `r` | replays the task |
| `continue` or `c` | moves to the next one |
| `quit` or `q` | aborts |

> 💡 **Traps**:
>
> - **`debugger: on_failed`** triggers the interactive debug **only
>   if** the task fails. To debug even on success: `debugger:
>   always`.
> - **Task vs play level**: `debugger:` can be at play-level (all
>   tasks) or task-level (this task only). Prefer
>   task-level: less intrusive.
> - **REPL blocked in CI**: `debugger:` works **only** in an
>   interactive terminal (TTY). In CI/cron, disable it via
>   `ANSIBLE_ENABLE_TASK_DEBUGGER=false`, or remove the directive.
>   Do not confuse it with `ANSIBLE_TASK_DEBUGGER_IGNORE_ERRORS`, which does the
>   OPPOSITE: it invokes the debugger even on a task carrying
>   `ignore_errors: true`.
> - **Variables modified via `task_vars[...]`** do not persist
>   beyond the task. To persist them: `set_fact` in a
>   later task.

## 🚀 Running

From the repo root:

```bash
ansible-playbook labs/troubleshooting/debugger/challenge/solution.yml
```

(the final version **with** `vars: { target_dir: /tmp }`, without the debugger).

## 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/debugger/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-debugger
```

## 💡 Going further

- Enable the debugger **globally**: `ANSIBLE_ENABLE_TASK_DEBUGGER=True ansible-playbook lab.yml`.
- `debugger: always`: opens the REPL **after each task** (slow, useful in TDD).
- **`ansible-lint`**: `ansible-lint --profile production challenge/solution.yml` must return green.
