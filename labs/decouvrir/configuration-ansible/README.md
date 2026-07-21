# Lab 03a — Ansible configuration (`ansible.cfg`, precedence, critical options)

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

🔗 [**Ansible configuration: ansible.cfg, precedence, critical options**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/ansible-config-fichier/)

Every mature Ansible project has an **`ansible.cfg`** that sets the **default options**: inventory path, SSH user, `become` behavior, callbacks, **forks**, **pipelining**, **roles_path**, **collections_path**. Without this file, Ansible uses **global default values** rarely suited to a project, and each run requires repetitive CLI arguments.

The RHCE EX294 exam asks you to **correctly configure** an Ansible project: create an `ansible.cfg`, understand the **precedence** (where it is read first), and know the **critical options** that change the behavior of runs. This page masters these 3 axes.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Understand** the loading precedence of `ansible.cfg` (`ANSIBLE_CONFIG` env > `./ansible.cfg` > `~/.ansible.cfg` > `/etc/ansible/ansible.cfg`).
2. **Create** a project `ansible.cfg` with the essential options (`inventory`, `remote_user`, `host_key_checking`, `forks`, `roles_path`, `collections_path`).
3. **Check** the active config with **`ansible-config dump --only-changed`**.
4. **Override** an option via an **environment variable** (`ANSIBLE_FORKS=20`).
5. **Enable** a callback (`ansible.posix.profile_tasks`) without touching a playbook.
6. **Distinguish** `[defaults]` vs `[ssh_connection]` vs `[privilege_escalation]` options.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.file -a "path=/tmp/lab03a-config.txt state=absent" 2>&1 | tail -2
```

## ⚙️ Target tree

```text
labs/decouvrir/configuration-ansible/
├── README.md                       ← this file (guided tutorial)
├── ansible.cfg                     ← (to create in exercise 2)
└── challenge/
    ├── README.md                   ← challenge instructions
    └── tests/
        └── test_configuration.py   ← tests pytest+testinfra
```

The learner writes `ansible.cfg`, `lab.yml` and `challenge/solution.yml` themselves.

## 📚 Exercise 1 — Precedence of `ansible.cfg` files

Ansible looks for its configuration file in **this order** (first found wins):

| Priority | Source | When to use it |
|----------|--------|------------------|
| 1 (max) | **`$ANSIBLE_CONFIG`** | Point to a custom file (CI, test) |
| 2 | **`./ansible.cfg`** in the current directory | **Recommended for a project** |
| 3 | **`~/.ansible.cfg`** | Global user preferences |
| 4 (min) | **`/etc/ansible/ansible.cfg`** | System config (rare) |

Check which file Ansible currently uses:

```bash
ansible --version | grep "config file"
```

🔍 **Observation**: if you run Ansible from a folder that contains an `ansible.cfg`, **that is the one used**. This is why a project `ansible.cfg` at the **repo root** is the standard 2026 pattern.

## 📚 Exercise 2 — Create a project `ansible.cfg`

Create `labs/decouvrir/configuration-ansible/ansible.cfg`:

```ini
[defaults]
inventory = ../../../inventory/hosts.yml
remote_user = student
host_key_checking = False
forks = 20
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-fact-cache
fact_caching_timeout = 7200
stdout_callback = yaml
callbacks_enabled = ansible.posix.profile_tasks, ansible.posix.timer
retry_files_enabled = False
deprecation_warnings = False
roles_path = ./roles:~/.ansible/roles
collections_path = ./collections:~/.ansible/collections

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -C -o ControlMaster=auto -o ControlPersist=60s
```

Check that this file is indeed read:

```bash
cd labs/decouvrir/configuration-ansible/
ansible --version | grep "config file"
# → config file = $ANSIBLE_TRAINING/labs/decouvrir/configuration-ansible.../ansible.cfg
```

🔍 **Observation**: 3 main sections: **`[defaults]`** (general behavior), **`[privilege_escalation]`** (sudo/become), **`[ssh_connection]`** (SSH transport). Each option has an **equivalent env variable**: `ANSIBLE_FORKS`, `ANSIBLE_HOST_KEY_CHECKING`, etc.

## 📚 Exercise 3 — Inspect the active config

```bash
ansible-config dump --only-changed
```

Typical output:

```text
DEFAULT_FORKS(/home/.../ansible.cfg) = 20
DEFAULT_GATHERING(/home/.../ansible.cfg) = smart
DEFAULT_HOST_LIST(/home/.../ansible.cfg) = ['/home/.../inventory/hosts.yml']
DEFAULT_REMOTE_USER(/home/.../ansible.cfg) = ansible
DEFAULT_STDOUT_CALLBACK(/home/.../ansible.cfg) = yaml
HOST_KEY_CHECKING(/home/.../ansible.cfg) = False
```

🔍 **Crucial observation**: **`--only-changed`** shows **only** the options that differ from the default. A **reference** to check what your `ansible.cfg` actually changes. Use it when debugging ("why this behavior?" → check the active config).

## 📚 Exercise 4 — Override an option via an env variable

```bash
# Without override: forks = 20 (defined in ansible.cfg)
ansible-config dump --only-changed | grep FORKS

# With override: forks = 50 for this command
ANSIBLE_FORKS=50 ansible-config dump --only-changed | grep FORKS
# → DEFAULT_FORKS(env: ANSIBLE_FORKS) = 50
```

🔍 **Observation**: the **env variable** has a **higher precedence** than the `ansible.cfg` file. Handy to **override on the spot** without modifying the file (CI, debug, ad-hoc test). The output of `ansible-config dump` shows the **source** in parentheses (`env:` or `path:`).

## 📚 Exercise 5 — Enable a callback (`profile_tasks`)

Create a simple `lab.yml`:

```yaml
---
- hosts: db1.lab
  gather_facts: false
  tasks:
    - ansible.builtin.shell: sleep 1
      changed_when: false
    - ansible.builtin.shell: sleep 0.5
      changed_when: false
    - ansible.builtin.ping:
```

Run it (with an `ansible.cfg` that enables `profile_tasks`):

```bash
ansible-playbook lab.yml
```

Output at the end of the run:

```text
TASK execution time:
   1.    sleep 1 ───────────────── 1.05s
   2.    sleep 0.5 ────────────── 0.52s
   3.    ping ─────────────────── 0.12s

Playbook run took 0 days, 0 hours, 0 minutes, 2 seconds
```

🔍 **Observation**: no need to modify the playbook to measure performance. **`callbacks_enabled = ansible.posix.profile_tasks`** in `ansible.cfg` is enough. An essential pattern to identify **bottlenecks** on a production fleet.

## 📚 Exercise 6 — `roles_path` and `collections_path`

Create a local role:

```bash
mkdir -p roles/check_disk/tasks
cat > roles/check_disk/tasks/main.yml <<'EOF'
---
- ansible.builtin.shell: df -h /
  register: disk
  changed_when: false
- ansible.builtin.debug:
    var: disk.stdout_lines
EOF
```

With `roles_path = ./roles:~/.ansible/roles` in `ansible.cfg`:

```yaml
- hosts: db1.lab
  gather_facts: false
  roles:
    - check_disk
```

Run it: Ansible **finds** the role in `./roles/` thanks to `roles_path`.

🔍 **Observation**: without `roles_path` configured, Ansible looks **only** in `~/.ansible/roles/` and `/usr/share/ansible/roles/`. Adding `./roles:` makes the **project-local** roles take priority: a standard pattern in 2026.

## 📚 Exercise 7 — Precedence env > cfg demonstrated

```bash
# Forks at 20 in ansible.cfg, 50 via env
ANSIBLE_FORKS=50 ansible-playbook lab.yml -v 2>&1 | head -3
```

Check the forks actually used via `ansible-config dump`.

🔍 **Observation**: the **precedence chain** is: env variables → project `ansible.cfg` → `~/.ansible.cfg` → `/etc/ansible/ansible.cfg` → default. **Always in this order**. It lets you **override** finely (env in CI, project file for the team, user file for personal use).

## 🔍 Observations to note

- **Precedence**: `ANSIBLE_CONFIG` env > `./ansible.cfg` > `~/.ansible.cfg` > `/etc/ansible/ansible.cfg`.
- **3 main sections**: `[defaults]`, `[privilege_escalation]`, `[ssh_connection]`.
- **`ansible-config dump --only-changed`** = inspection of the effective config.
- **Env variables**: `ANSIBLE_FORKS`, `ANSIBLE_HOST_KEY_CHECKING`, etc. override the file.
- **Callbacks** enabled via `callbacks_enabled = ansible.posix.profile_tasks, ...`.
- **`roles_path` / `collections_path`** make the **project-local** resources take priority.

## 🤔 Reflection questions

1. What happens if **two** `ansible.cfg` exist: one in `./` and one in `~/.ansible.cfg`?
2. Why is `host_key_checking = False` **acceptable in a lab** but **dangerous in production**?
3. Which `[ssh_connection]` option is **incompatible** with `Defaults requiretty` in `/etc/sudoers`?
4. How do you **disable** a callback temporarily without modifying `ansible.cfg`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): create an `ansible.cfg` that enables `profile_tasks`, forces `forks=20`, and drop a proof file that contains the result of `ansible-config dump --only-changed`.

## 💡 Going further

- **Lab 91**: advanced performance tuning (pipelining, ControlPersist).
- **`ansible-config view`**: displays the effective `ansible.cfg` with comments.
- **`ansible-config init --disabled > ansible.cfg`**: generates an empty config file with **all** the options documented.
- **Exhaustive env variables**: see `ansible-config list` for the complete list.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/decouvrir/configuration-ansible/lab.yml
ansible-lint --profile production labs/decouvrir/configuration-ansible/challenge/solution.yml
```

> 💡 **Tip**: `ansible-lint` does not check the content of `ansible.cfg`. To validate the **syntax**: `ansible-config view` returns an error if the file is malformed.
