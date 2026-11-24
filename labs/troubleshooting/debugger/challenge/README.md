# Ninety tasks to replay for a one-word fix

## The situation

The deployment play dies at task 91 on **db1.lab**: an undefined variable, and no
way to know what it should have been. So you guess, edit the YAML, and re-run the
whole thing from the top. Ninety tasks, twelve minutes, wrong guess. Second
attempt: ninety tasks, twelve minutes. Every iteration of a one-word fix costs a
coffee break, and the run gives you no chance to look around at the moment it
actually knows something.

Your mission, from **control-node.lab**:

1. Arm the play so a failing task **opens a session instead of ending the run**,
   at the exact point where the state is still available.
2. From there, inspect what the run knows: the task as it was resolved, the
   variables in scope, and the module's own result.
3. Fix the failure **live**, by supplying the missing value in the running session
   rather than in the file, and **replay just that task** to confirm your guess.
4. Once the run finishes, commit the fix to the playbook properly, so the value no
   longer depends on someone being at the keyboard.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/debugger-interactif/ (in French)

## 🎯 Challenge — Fixing a missing variable with the debugger

### ✅ Objective

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

### 🧩 Stuck?

```bash
dsoxlab hint troubleshooting-debugger
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Running

From the repo root:

```bash
ansible-playbook labs/troubleshooting/debugger/challenge/solution.yml
```

(the final version **with** `vars: { target_dir: /tmp }`, without the debugger).

### 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/debugger/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean troubleshooting-debugger
```

### 💡 Going further

- Enable the debugger **globally**: `ANSIBLE_ENABLE_TASK_DEBUGGER=True ansible-playbook lab.yml`.
- `debugger: always`: opens the REPL **after each task** (slow, useful in TDD).
- **`ansible-lint`**: `ansible-lint --profile production challenge/solution.yml` must return green.
