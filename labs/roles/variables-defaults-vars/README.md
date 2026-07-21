# Lab 59 — Variables `defaults/` vs `vars/` in a role

> 💡 **Prerequisite**: the 4 lab VMs respond to the Ansible ping.
>
> ```bash
> ansible all -m ansible.builtin.ping
> ```

## 🧠 Recap

🔗 [**Variables defaults vs vars**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/variables-defaults-vars/)

An Ansible role exposes **input variables** that the user can parameterize. Two directories for that:

- **`defaults/`**: default values, **overridable**. Priority **2** out of 22 in the Ansible precedence (very low).
- **`vars/`**: internal constants, **NON-overridable**. Priority **18** out of 22 (very high).

**Simple rule**: if the user MUST be able to change the value, it goes in `defaults/`. If the value is an internal detail (system path, OS mapping), it goes in `vars/`.

This lab extends the `webserver` role from **lab 58** to demonstrate this distinction and the **precedence**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Distinguish **`defaults/main.yml`** (overridable) from **`vars/main.yml`** (internal).
2. Wire **variables to tasks** via `{{ var_name }}`.
3. Override the variables from a **playbook** with `vars:`.
4. Understand the **precedence**: `defaults/` < `vars: of the play` < `vars/`.
5. Use the variables in a **Jinja2 template** (`nginx.conf.j2`).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/roles/variables-defaults-vars
```

## ⚙️ Target tree

```text
labs/roles/variables-defaults-vars/
├── README.md
├── playbook.yml          ← demo: uses the DEFAULT values
├── roles/
│   └── webserver/
│       ├── tasks/main.yml
│       ├── defaults/main.yml    ← overridable
│       ├── vars/main.yml        ← internal
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       ├── templates/
│       │   └── nginx.conf.j2    ← template that CONSUMES the variables
│       └── README.md
└── challenge/
    ├── README.md
    ├── solution.yml      ← override: webserver_listen_port: 8080
    ├── roles/            ← symlink to ../roles
    └── tests/
        └── test_variables.py
```

## 📚 Exercise 1 — Read `defaults/main.yml`

```bash
cat roles/webserver/defaults/main.yml
```

8 variables with default values. All prefixed by **`webserver_`** (role-name convention to avoid collisions).

🔍 **Observation**: these 8 variables are **public**: the role's user can redefine them all in their playbook or their `group_vars/`.

## 📚 Exercise 2 — Read `vars/main.yml`

```bash
cat roles/webserver/vars/main.yml
```

4 variables with a **double underscore** (`__webserver_config_dir`, etc.). A convention to signal **"internal use, do not modify"**.

🔍 **Observation**: these 4 variables are **system paths** that do not depend on the user's choice. If they were in `defaults/`, a user could break the role by redefining `__webserver_html_dir`.

## 📚 Exercise 3 — Read the `nginx.conf.j2` template

```bash
cat roles/webserver/templates/nginx.conf.j2
```

The template consumes **5 different** variables:

- `{{ webserver_worker_processes }}` (defaults/)
- `{{ webserver_worker_connections }}` (defaults/)
- `{{ webserver_listen_port }}` (defaults/)
- `{{ __webserver_log_dir }}` (vars/)
- `{{ __webserver_html_dir }}` (vars/)

🔍 **Observation**: the template uses variables from `defaults/` and `vars/` **interchangeably**. For Jinja, they are just variables: the precedence distinction happens upstream when Ansible resolves the values.

## 📚 Exercise 4 — Run with the DEFAULT values

```bash
ansible-playbook playbook.yml
```

The playbook **overrides no variable**. The role runs with:

- `webserver_listen_port: 80` (default from `defaults/main.yml`)
- `webserver_index_content: "<h1>Hello from web1.lab</h1>"` (default)

🔍 **Observation**: on web1, nginx listens on **80**. Test:

```bash
curl http://web1.lab/
# → <h1>Hello from web1.lab</h1>
```

## 📚 Exercise 5 — Override from the playbook

Now, create a playbook that **overrides** some variables:

```yaml
---
- name: Webserver avec port custom
  hosts: web1.lab
  become: true
  roles:
    - role: webserver
      vars:
        webserver_listen_port: 9090
        webserver_index_content: "Custom message override"
```

Run this playbook (temporarily replacing `playbook.yml`). Now nginx listens on **9090** instead of 80.

🔍 **Observation**: the **play**'s `vars:` **won** over the values of `defaults/main.yml`. This is precedence in action.

## 📚 Exercise 6 — Two almost identical syntaxes, two opposite results

The role's `vars/main.yml` "protects" its internal constants. Against what, exactly?
Make the bet before running, then measure. It is the subtlest pitfall of roles.

**Case A: `vars:` at PLAY level**

```yaml
- name: Override au niveau du play
  hosts: web1.lab
  become: true
  vars:
    __webserver_html_dir: /tmp/test    # ← at PLAY level
  roles:
    - role: webserver
```

**Case B: `vars:` under the role entry** (two indentation characters further)

```yaml
- name: Override sous l'entrée de rôle
  hosts: web1.lab
  become: true
  roles:
    - role: webserver
      vars:
        __webserver_html_dir: /tmp/test    # ← under "- role:"
```

Run both, and look at where the welcome page lands.

🔍 **The result is surprising, and that is the whole point**:

| Case | What it really is | Precedence | Result |
| --- | --- | --- | --- |
| **A**: `vars:` of the play | play vars | **12** | the override is **IGNORED**, the role's `vars/` (15) wins |
| **B**: `vars:` under `- role:` | **role params** (these are NOT play vars) | **20** | the override **APPLIES**, it beats the role's `vars/` (15) |

**The lesson**: `vars/main.yml` does **not** protect a role "against the user". It
protects it against a `vars:` placed at play level, and **against nothing else**. Whoever
passes the variable as a role parameter wins, as `--extra-vars` (22) does in exercise 7.

The pitfall is not the precedence, it is the **syntax**: two lines apart in the YAML,
and the variable changes category. A `vars:` under `- role:` is not a play `vars:`.

> **Check it yourself**, do not take my word for it: it is exactly what
> `VariableManager.get_vars()` of ansible-core does, merging in the order `play vars`, then
> `role vars`, then `role params`. The last merged overwrites the previous ones.

## 📚 Exercise 7 — Override with `--extra-vars` (priority 22, the top)

```bash
ansible-playbook playbook.yml \
  --extra-vars "webserver_listen_port=12345"
```

`--extra-vars` is **priority 22**, above everything. This time, nginx listens on 12345.

🔍 **Observation**: `--extra-vars` can override **EVERYTHING**, even the role's `vars/main.yml`:

```bash
ansible-playbook playbook.yml \
  --extra-vars "__webserver_html_dir=/tmp/extra"
```

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name; `ansible-lint --profile
  production` checks it.
- **Targeting convention**: this lab targets db1.lab; to adapt to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then re-run.
- **Isolated reset**: `dsoxlab clean <lab-id>` at the root of the lab cleanly
  uninstalls what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. In which case do you put a variable in `vars/` rather than `defaults/`?

2. Why prefix variables with the role name (`webserver_listen_port`)?

3. If the same variable is defined in `host_vars/web1.lab.yml` AND in the play's `vars:`, who wins?

4. How do you **test the effect** of a variable change without re-running the full deployment?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to **override 3 variables** in a playbook that targets `db1.lab`:

- `webserver_listen_port: 8080`
- `webserver_worker_connections: 2048`
- `webserver_index_content: "Custom page from challenge lab 59 on {{ inventory_hostname }}"`

Automated tests via `pytest+testinfra` (5 tests):

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Read the official precedence**: 22 levels documented [here](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence).
- **Directory pattern** for `defaults/`: on complex roles, split into several files (`defaults/main.yml`, `defaults/network.yml`, `defaults/security.yml`).
- **Distro-specific `vars/`**: `vars/RedHat.yml`, `vars/Debian.yml` loaded dynamically via `include_vars: "{{ ansible_os_family }}.yml"`, a common pattern for multi-distro roles.
- **Lab 60** will add **handlers** to the role: reactive actions triggered by `notify:`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/roles/variables-defaults-vars/lab.yml
ansible-lint labs/roles/variables-defaults-vars/challenge/solution.yml
ansible-lint --profile production labs/roles/variables-defaults-vars/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
