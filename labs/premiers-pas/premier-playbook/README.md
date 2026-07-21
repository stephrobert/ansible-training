# Lab 04 — First playbook (install nginx on the webservers)

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

🔗 [**First Ansible playbook: install nginx, open port 80, start the service**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premier-playbook/)

This is your **first real playbook**, the one where you write the YAML yourself. The blog page presents the **anatomy of a playbook**:

```yaml
---
- name: <play name>            # free text, shown in the console
  hosts: <pattern>             # which managed nodes to target (e.g. webservers, all, web1.lab)
  become: true                 # sudo (root elevation)
  gather_facts: true           # gather facts at startup

  tasks:                       # list of tasks, run in order
    - name: <description>      # always name your tasks!
      ansible.builtin.<module>:
        param1: valeur1
        param2: valeur2
```

Each **task** calls a **module**. A module is a mini-program that does **one single thing** (install a package, copy a file, start a service...). You will use 5 of them in this lab: `dnf`, `systemd`, `firewalld`, `uri`, `debug`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a YAML playbook that **chains 5 tasks**.
2. Run it with `ansible-playbook` on the `webservers` group.
3. Read the **`PLAY RECAP`** and identify `ok` / `changed` / `failed`.
4. Check **idempotence** on the second run (`changed=0`).
5. Capture a task's output into a variable with **`register:`**.
6. Test from outside that the web service responds.

## 🔧 Preparation

Check that the 2 webservers are reachable:

```bash
cd $ANSIBLE_TRAINING
ansible webservers -m ansible.builtin.ping
```

Expected response: 2 `pong` (one for `web1.lab`, one for `web2.lab`).

> 💡 All `ansible-playbook` commands are run **from the repo root**: that is what lets the inventory resolve `{{ inventory_dir }}/../ssh/id_ed25519`.

## ⚙️ Target tree layout (to build yourself)

```text
labs/premiers-pas/premier-playbook/
├── README.md          ← this file (already present)
├── playbook.yml       ← TO CREATE: your first playbook
└── challenge/
    ├── README.md      ← final challenge (already present)
    └── tests/
        └── test_*.py  ← pytest+testinfra (already present)
```

## 📚 Exercise 1 — The playbook skeleton

Create `labs/premiers-pas/premier-playbook/playbook.yml` with the skeleton below. The 5 tasks come next, in order.

```yaml
---
- name: Déployer nginx sur les webservers
  hosts: webservers
  become: true
  gather_facts: true

  tasks:
    # Vous allez écrire les 5 tâches ci-dessous, dans cet ordre.
```

🔍 **Observation**: every line of the skeleton matters:

- **`hosts: webservers`** → targets the group defined in `inventory/hosts.yml` (so `web1.lab` + `web2.lab`).
- **`become: true`** → the whole play runs as root via `sudo`. Without it, `dnf install` fails with "Permission denied".
- **`gather_facts: true`** → Ansible gathers ~200 variables on each host at startup (OS, IP, memory, etc.). It is the default, but we make it explicit here to mark this step clearly.

## 📚 Exercise 2 — Task 1: install nginx

In `tasks:`, add the first task. The `ansible.builtin.dnf` module installs (or removes) an RPM package.

Hints:

- Module: `ansible.builtin.dnf` (mandatory RHCE FQCN).
- `name: nginx`
- `state: present` (present: install if absent, do nothing otherwise).

To help you, run the doc:

```bash
ansible-doc ansible.builtin.dnf | less
```

🔍 **Observation to anticipate**: on the first run, this task will show `changed` (package installed). On the second run, `ok` (already present).

## 📚 Exercise 3 — Task 2: start and enable nginx

The package is installed but **the service is not started** (the `nginx` package on RHEL/AlmaLinux does not auto-start). Add an `ansible.builtin.systemd` task that:

- `name: nginx`
- `state: started` (start now)
- `enabled: true` (enable at boot)

🔍 **Observation to anticipate**: `state: started` ≠ `state: restarted`. `started` is **idempotent** (does nothing if already active), `restarted` restarts **on every run**. You will use `restarted` later via **handlers** (lab 06).

## 📚 Exercise 4 — Task 3: open port 80 in firewalld

AlmaLinux 9 has `firewalld` enabled by default, so port 80 is **closed** even if nginx listens on it. Add an `ansible.posix.firewalld` task that opens the `http` service:

- `service: http` (firewalld knows `http` as an alias for port 80/tcp)
- `permanent: true` (rule persistent across reboot)
- `immediate: true` (rule applied right away, without `firewall-cmd --reload`)
- `state: enabled`

> ⚠️ **Classic trap**: if you forget `immediate: true`, the rule is written but **not applied**. The test from your workstation will return `Connection refused` until the next firewall reload.

🔍 **Observation to anticipate**: the `ansible.posix.firewalld` module (not `ansible.builtin`) comes from the `ansible.posix` collection installed in lab 02.

## 📚 Exercise 5 — Task 4: test with `uri` and capture the response

Before declaring victory, you **test**. The `ansible.builtin.uri` module makes an HTTP request **from the managed node**:

- `url: http://localhost`
- `status_code: 200` (fails if the returned code is not 200)
- **`register: nginx_response`** (captures the whole response into a variable)

🔍 **Observation to anticipate**: `register:` is the bridge between a task and the next one. The `nginx_response` variable contains a dict with `status`, `url`, `content`, `elapsed`, etc. You use it in the next task.

## 📚 Exercise 6 — Task 5: display the result with `debug`

To confirm everything is OK, display the captured HTTP code. `ansible.builtin.debug` module:

- `msg: "nginx répond avec le code {{ nginx_response.status }} sur {{ inventory_hostname }}"`

Hints:

- `{{ nginx_response.status }}` → the `status` attribute of the dict captured in exercise 5.
- `{{ inventory_hostname }}` → magic variable = name of the current host in the Ansible loop.
- The `{{ }}` are Jinja2 interpolation syntax.

## 📚 Exercise 7 — Run the playbook

From the repo root:

```bash
ansible-playbook labs/premiers-pas/premier-playbook/playbook.yml
```

🔍 **Observation**: the `PLAY RECAP` on the **first run** looks like:

```text
PLAY RECAP *********************************************************************
web1.lab    : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web2.lab    : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Column breakdown:

- **`ok=6`**: 6 tasks returned an OK status (your 5 tasks + the initial `gather_facts`).
- **`changed=3`**: 3 tasks **modified** the system state (dnf install, systemd start, firewalld opening). The `uri` and `debug` tasks modify nothing, they are `ok` but not `changed`.
- **`failed=0`**: no error.

## 📚 Exercise 8 — Check idempotence

Rerun the same command **immediately**:

```bash
ansible-playbook labs/premiers-pas/premier-playbook/playbook.yml
```

🔍 **Observation**: the `PLAY RECAP` must show **`changed=0`**:

```text
web1.lab    : ok=6    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

This is the **mechanical proof of idempotence** (seen in lab 01). Your 3 "modifying" tasks saw that the desired state was already applied and did **nothing**. That is what makes Ansible safe to rerun 100 times.

## 📚 Exercise 9 — Test from your workstation

From your workstation (the control node):

```bash
curl -I http://10.10.20.21
curl -I http://10.10.20.22
```

🔍 **Observation**: you must see `HTTP/1.1 200 OK` and a `Server: nginx/...` header. If you get `Connection refused`, check exercise 4 (firewalld's `immediate: true`).

## 🔍 Observations to note

- A **minimal playbook** = `name` + `hosts` + `tasks`. `become` and `gather_facts` are options (with defaults).
- **FQCN** (`ansible.builtin.dnf`) instead of the short name (`dnf`): mandatory for RHCE, recommended everywhere. Guarantees you call the intended module.
- The **`PLAY RECAP`** is your **dashboard**: `ok`, `changed`, `failed`, `unreachable`. A task can be `ok` without being `changed` (read-only, a check).
- `state: started` (idempotent) ≠ `state: restarted` (systematic action). Same for `present` / `latest` on `dnf`.
- **`register:`** + **`{{ var.attribute }}`** = the basic pattern to chain two tasks.
- `ansible.builtin.*` ships with `ansible-core`. The other collections (e.g. `ansible.posix.firewalld`) must be installed via `ansible-galaxy`.

## 🤔 Reflection questions

1. You change `state: present` to `state: latest` on the `dnf` task. What happens on the second run? Is it still idempotent? Why?

2. You forget `become: true` at the play level. Which task fails first, and with what message? (Hint: `dnf install` requires root.)

3. You want to **run the `uri` test** only if nginx was just started (and not on every run). Which Ansible keyword allows that? (Hint: you will see it in lab 20, `when:`.)

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to **rewrite the same logic** for `nginx` on `db1.lab`, but on the non-standard port **8888** instead of the webservers' port 80. A simple port change surfaces one more lock: SELinux. The `pytest+testinfra` tests will automatically check your solution:

```bash
pytest -v labs/premiers-pas/premier-playbook/challenge/tests/
```

This is the chance to test whether you really understood the skeleton, or just copied it.

## 💡 Going further

- **`--check` mode** (lab 08): `ansible-playbook playbook.yml --check` simulates without modifying. Very useful in pre-prod.
- **Tags** (lab 07): tag each task to run selectively (`--tags install` runs only the install task).
- **Handlers** (lab 06): replace the `state: started` task with a **handler** triggered only when a config file changes. This is the real production pattern.
- **Variables** (lab 12): externalize `nginx`, `http`, `localhost` into reusable variables.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/premiers-pas/premier-playbook/lab.yml

# Lint your challenge solution
ansible-lint labs/premiers-pas/premier-playbook/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/premiers-pas/premier-playbook/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
