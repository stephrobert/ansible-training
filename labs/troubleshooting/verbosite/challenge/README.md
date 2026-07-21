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

## 🧩 Hints

### Step 1 — Create `ansible.cfg` at the lab level

```ini
[defaults]
stdout_callback = ???
callbacks_enabled = ansible.posix.profile_tasks, ???

[callback_profile_tasks]
task_output_limit = ???
```

### Step 2 — `solution.yml` skeleton

```yaml
---
- name: Challenge 89 — profile 3 tâches
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: ???                                   # task 1
      ansible.builtin.shell: sleep 1
      changed_when: false

    - name: ???                                   # task 2
      ansible.builtin.shell: ???
      changed_when: false

    - name: ???                                   # task 3: drops the proof file
      ansible.builtin.copy:
        dest: /tmp/lab89-profile.txt
        content: |
          ???
          ???
          ???
        owner: ???
        group: ???
        mode: ???
```

### Step 3 — Enable the profile via `ANSIBLE_CONFIG`

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/challenge/solution.yml
```

> 💡 **Traps**:
>
> - **`-v` to `-vvvv`**: 4 levels. `-v` = per-host recap; `-vv` = +
>   variables; `-vvv` = + SSH commands; `-vvvv` = + connection
>   establishment.
> - **`ANSIBLE_DEBUG=1`**: massive output (Ansible internal debug). Use it
>   **only** when `-vvvv` is not enough.
> - **Callback plugins**: `yaml`, `default`, `unixy`, `dense`, `null`,
>   `oneline`, `selective`. Set in `ansible.cfg` via
>   `stdout_callback = yaml`.
> - **`no_log: true`** hides the output even under `-vvvv`: secret
>   protection. Keep it in prod.

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
  (with `stdout_callback = yaml`): the callback that is the whole point of the lab.

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-verbosite
```

## 💡 Going further

- **Several combined callbacks**: add `ansible.posix.timer` for total time.
- **Timing capture**: redirect the `ansible-playbook` output to a file, parse it with `grep -E 'TASK execution time'`.
- **`ansible-lint`**: `ansible-lint --profile production challenge/solution.yml` must return green.
