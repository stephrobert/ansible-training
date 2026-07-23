# Lab 89 — Progressive verbosity (`-v` to `-vvvv`) and callback plugins

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**Ansible verbosity: -v / -vv / -vvv / -vvvv**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/verbosite-vvv/)

When a playbook fails, **the verbosity flags** are your first tools. Each level opens a new notch of information:

| Flag | Provides |
| --- | --- |
| `-v` | Enriched task results |
| `-vv` | Actual arguments passed to the module (post-Jinja2-template) |
| `-vvv` | SSH connection details, module tmp path on the target |
| `-vvvv` | Connection plugin internals, raw scp/sftp, ControlMaster |

On top of that, **callback plugins** like `ansible.posix.profile_tasks` measure the **time per task** without touching the playbook code. Mastering these two levers solves 80% of production errors.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Choose** the right `-v` level based on the symptom (Jinja variable vs SSH vs other).
2. **Enable** a `profile_tasks` callback via `ansible.cfg` to measure performance.
3. **Distinguish** the **post-template** arguments (`-vv`) from the SSH connections (`-vvv`).
4. **Enable** `callback_result_format = yaml` for readable multi-line output.
5. **Leak a secret** by accident **and** understand why `no_log: true` is mandatory.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab89-* state=absent" 2>&1 | tail -2
```

## ⚙️ Target tree layout

```text
labs/troubleshooting/verbosite/
├── README.md                       ← this file (guided tutorial)
├── ansible.cfg                     ← (to create in exercise 4)
└── challenge/
    ├── README.md                   ← challenge brief with skeleton
    └── tests/
        └── test_verbosite.py       ← pytest+testinfra tests
```

The learner writes `lab.yml` (over the exercises) and `challenge/solution.yml` themselves.

## 📚 Exercise 1 — Trigger a Jinja2 error and observe it with `-v`

Create a `lab.yml` with a **misnamed variable**:

```yaml
---
- name: Lab 89 — debug verbosité
  hosts: db1.lab
  gather_facts: false
  vars:
    db_user: "appuser"
  tasks:
    - name: Erreur volontaire — variable inexistante
      ansible.builtin.debug:
        msg: "User: {{ db_use }}"     # ← intentional typo (db_use instead of db_user)
```

Run in normal mode:

```bash
ansible-playbook labs/troubleshooting/verbosite/lab.yml
```

Typical output:

```text
fatal: [db1.lab]: FAILED! => {"msg": "The task includes an option with an undefined variable. The error was: 'db_use' is undefined..."}
```

🔍 **Observation**: without `-v`, the message says **where** it breaks but **not** what the variable contained before templating. Not enough for more complex Jinja2 cases.

## 📚 Exercise 2 — See resolved variables with `-vv`

```bash
ansible-playbook labs/troubleshooting/verbosite/lab.yml -vv
```

Additional output:

```text
task path: $ANSIBLE_TRAINING/labs/troubleshooting/verbosite…/lab.yml:7
The error appears to be in '…': line 7, column 7
…
TASK [Erreur volontaire — variable inexistante] ***
fatal: [db1.lab]: FAILED! => {"msg": "...db_use is undefined..."}
```

🔍 **Observation**: `-vv` adds the **file:line path** and the **actual arguments** passed to each module. It is the **everyday default** level when developing a playbook.

## 📚 Exercise 3 — Diagnose an SSH failure with `-vvv`

Modify `lab.yml` to target a nonexistent host:

```yaml
- name: Échec SSH volontaire
  hosts: nonexistent.lab
  gather_facts: false
  tasks:
    - ansible.builtin.ping:
```

Run:

```bash
ansible-playbook labs/troubleshooting/verbosite/lab.yml -vvv
```

Typical output:

```text
ESTABLISH SSH CONNECTION FOR USER: ansible
SSH: EXEC ssh -C -o ControlMaster=auto -o ControlPersist=60s …
ssh: Could not resolve hostname nonexistent.lab: Name or service not known
```

🔍 **Observation**: `-vvv` shows the **exact SSH command** Ansible runs. Reproduce it by hand with `ssh -vvv user@host` to bypass Ansible entirely. It is the **essential** level for diagnosing network issues.

## 📚 Exercise 4 — Enable the `profile_tasks` callback

Create `ansible.cfg` at the lab root:

```ini
[defaults]
callback_result_format = yaml
callbacks_enabled = ansible.posix.profile_tasks, ansible.posix.timer

[callback_profile_tasks]
task_output_limit = 10
```

With a playbook that runs several tasks:

```yaml
---
- hosts: db1.lab
  gather_facts: false
  tasks:
    - ansible.builtin.shell: sleep 2
      changed_when: false
    - ansible.builtin.shell: sleep 1
      changed_when: false
    - ansible.builtin.ping:
```

Run:

```bash
ANSIBLE_CONFIG=labs/troubleshooting/verbosite/ansible.cfg \
  ansible-playbook labs/troubleshooting/verbosite/lab.yml
```

Output at the end of the run:

```text
TASK execution time:
   1.    sleep 2 ──────────────── 2.05s
   2.    sleep 1 ──────────────── 1.04s
   3.    ping ──────────────────── 0.82s
Playbook run took 0 days, 0 hours, 0 minutes, 4 seconds
```

🔍 **Observation**: `profile_tasks` sorts tasks by descending duration. **Essential** for spotting the slowest tasks on a production fleet. The `timer` callback adds the playbook's **total time**.

## 📚 Exercise 5 — `callback_result_format = yaml` for readable output

Without the `yaml` callback, a complex `set_fact` shows:

```text
ok: [db1.lab] => {"ansible_facts": {"my_data": [{"name": "alice", "age": 30}, {"name": "bob", "age": 25}]}}
```

With `callback_result_format = yaml`:

```yaml
ok: [db1.lab] => 
  ansible_facts:
    my_data:
      - name: alice
        age: 30
      - name: bob
        age: 25
```

🔍 **Observation**: **multi-line** output, human-readable, ideal for debugging. Enable it by default in `ansible.cfg`.

## 📚 Exercise 6 — The `-v` trap that leaks a secret

With this playbook (without `no_log:`):

```yaml
- ansible.builtin.shell: 'echo "Secret token: super_secret_token_42"'
  register: out
- debug: var=out.stdout
```

Run with `-v`:

```bash
ansible-playbook lab.yml -v
```

Output:

```text
ok: [db1.lab] =>
  out.stdout: "Secret token: super_secret_token_42"
```

🔍 **Crucial observation**: **`-v` can reveal secrets** in the output. **Always** add **`no_log: true`** on tasks that handle credentials:

```yaml
- ansible.builtin.shell: 'echo "Secret token: super_secret_token_42"'
  register: out
  no_log: true                  # ← blocks the output under -v
```

## 🔍 Observations to note

- **`-v`** = everyday dev level to see detailed results.
- **`-vv`** = file path + templated args. Jinja2 bug → use `-vv`.
- **`-vvv`** = exact SSH command. Network / connection bug → use `-vvv`.
- **`-vvvv`** = connection plugin internals. Very rare, mostly for ControlMaster.
- **Callbacks**: `profile_tasks` + `timer` + `callback_result_format=yaml` in `ansible.cfg`.
- **`no_log: true`** systematically on any task handling a secret.

## 🤔 Reflection questions

1. At which verbosity level do you see the **Jinja2-substituted arguments**?
2. Why is `-vvvv` rarely useful in production?
3. What happens if `no_log: true` is placed on the **module** instead of the **task**?
4. How do you **disable colors** in the output for a CI log? (Hint: `ANSIBLE_FORCE_COLOR=0` or `--no-color`).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): create a playbook with **3 tasks measured** by `profile_tasks` that drops a timing file on `db1.lab`.

## 💡 Going further

- **Lab 90**: interactive `(debug)` REPL debugger.
- **Lab 91**: broken idempotence + forks/pipelining tuning.
- **`ANSIBLE_DEBUG=1` variable**: Ansible engine debug (very verbose).
- **`ANSIBLE_KEEP_REMOTE_FILES=1`**: keeps the modules on the target for inspection (lab 91).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/troubleshooting/verbosite/lab.yml
ansible-lint labs/troubleshooting/verbosite/challenge/solution.yml
ansible-lint --profile production labs/troubleshooting/verbosite/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices.
