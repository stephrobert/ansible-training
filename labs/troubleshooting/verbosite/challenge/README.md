# Twenty minutes of guessing, and a password in the CI logs

## The situation

A task fails on **db1.lab** with a message that says nothing useful, and the team
reflex is to re-run it with every `-v` the keyboard can hold. That dumps thousands
of lines, and buries the one that mattered. Then someone noticed the real damage:
a task handling a token had printed its arguments in full into a log everyone can
read. Verbosity is a scalpel, and the team is using it as a hammer, on a playbook
that was never told to keep its mouth shut.

Your mission, from **control-node.lab**:

1. Match the **verbosity level to the symptom**: which level shows the arguments a
   module actually received after templating, and which one is about the SSH
   connection and has nothing to say about your bug.
2. Enable **task profiling** on a play of three measurable tasks against
   **db1.lab**, without touching the tasks themselves, and read the timings.
3. Make the output legible: switch the terminal callback for one a human can scan
   during an incident, and drop the profiling proof into a file on the target.
4. Observe what a **missing `no_log`** leaks at higher verbosity, and fix it.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/verbosite-vvv/ (in French)

## 🎯 Challenge — Profile 3 tasks on `db1.lab`

### ✅ Objective

Write a playbook that runs **3 measurable tasks** on `db1.lab`, enable the `profile_tasks` callback, and drop a `/tmp/lab89-profile.txt` file containing the **names** of the 3 tasks in the order they were executed.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab89-profile.txt` |
| Permissions | `0644`, owner `root` |
| Content | The 3 task names separated by `\n` (one per line) |
| Enabled callbacks | `ansible.posix.profile_tasks` (visible in the output) |

### 🧩 Stuck?

```bash
dsoxlab hint troubleshooting-verbosite
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Running

From the repo root:

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/verbosite/challenge/tests/
```

The pytest+testinfra test validates:

- `/tmp/lab89-profile.txt` exists on `db1.lab` with mode `0644`.
- The file contains **exactly 3** non-empty **lines** (the 3 task names).
- The lab-level `ansible.cfg` exists and enables `ansible.posix.profile_tasks`
  (with `callback_result_format = yaml`): the callback that is the whole point of the lab.

### 🧹 Reset

```bash
dsoxlab clean troubleshooting-verbosite
```

### 💡 Going further

- **Several combined callbacks**: add `ansible.posix.timer` for total time.
- **Timing capture**: redirect the `ansible-playbook` output to a file, parse it with `grep -E 'TASK execution time'`.
- **`ansible-lint`**: `ansible-lint --profile production challenge/solution.yml` must return green.
