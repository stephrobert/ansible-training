# 🎯 Challenge — Combine `import_tasks` + `include_tasks` + a loop

## ✅ Objective

Write a playbook that combines the **3 patterns** (`import_tasks` static + `include_tasks` with `loop:` + 1 separate task) and drops **4 files** on `db1.lab` that prove the execution of each mechanism.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| File 1 (import_tasks) | `/tmp/lab30a-import.txt` (`step: import-static`) |
| Files 2, 3, 4 (include_tasks loop) | `/tmp/lab30a-loop-1.txt`, `lab30a-loop-2.txt`, `lab30a-loop-3.txt` |
| Permissions | `0644`, owner `root` |
| Mechanisms used | **`ansible.builtin.import_tasks`** + **`ansible.builtin.include_tasks`** with `loop:` |

## 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-import-include
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/import-include/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/import-include/challenge/tests/
```

The pytest test validates:

- `/tmp/lab30a-import.txt` exists + contains `import-static`.
- `/tmp/lab30a-loop-1.txt`, `-2.txt`, `-3.txt` exist + contain `iteration: <N>`.
- The playbook does use both `import_tasks` AND `include_tasks` (not a mix).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-import-include
```

## 💡 Going further

- **`apply:`** on `include_tasks`: inject `tags`/`become`/`when` into all the tasks **internal** to the included file.
- **`import_playbook`**: **plays** level, to orchestrate several playbooks. Not usable in `tasks:`.
- **`include_role` + `loop:`**: advanced pattern to apply a role several times with different vars.
