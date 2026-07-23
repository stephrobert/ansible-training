# 🎯 Challenge — Profile 3 tasks on `db1.lab`

## ✅ Objective

Write a playbook that runs **3 measurable tasks** on `db1.lab`, enable the `profile_tasks` callback, and drop a `/tmp/lab89-profile.txt` file containing the **names** of the 3 tasks in the order they were executed.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab89-profile.txt` |
| Permissions | `0644`, owner `root` |
| Content | The 3 task names separated by `\n` (one per line) |
| Enabled callbacks | `ansible.posix.profile_tasks` (visible in the output) |

## 🧩 Stuck?

```bash
dsoxlab hint troubleshooting-verbosite
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Running

From the repo root:

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/verbosite/challenge/tests/
```

The pytest+testinfra test validates:

- `/tmp/lab89-profile.txt` exists on `db1.lab` with mode `0644`.
- The file contains **exactly 3** non-empty **lines** (the 3 task names).
- The lab-level `ansible.cfg` exists and enables `ansible.posix.profile_tasks`
  (with `callback_result_format = yaml`): the callback that is the whole point of the lab.

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-verbosite
```

## 💡 Going further

- **Several combined callbacks**: add `ansible.posix.timer` for total time.
- **Timing capture**: redirect the `ansible-playbook` output to a file, parse it with `grep -E 'TASK execution time'`.
- **`ansible-lint`**: `ansible-lint --profile production challenge/solution.yml` must return green.
