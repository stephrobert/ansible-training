# Lab 58 — Create your first Ansible role (the `webserver` running-theme role)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```

## 🧠 Recap

🔗 [**Create your first Ansible role**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/creer-premier-role/)

An **Ansible role** is the unit of reuse: a structured directory that packages tasks, variables, templates, handlers and tests around a single goal. It is **the equivalent of a Terraform module** on the Ansible side.

This lab introduces the **running-theme role** `webserver` that will be enriched across labs 58 → 64. By the end of this series, you will have a **production-ready** role tested in TDD with Molecule and tox.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Generate a role's structure with **`ansible-galaxy role init`**.
2. Identify a role's **10 standard** directories.
3. Write the **main tasks** in `tasks/main.yml`.
4. Define the **default variables** in `defaults/main.yml`.
5. Document the role through **`meta/main.yml`** and **`README.md`**.
6. Call the role from a playbook with **`roles:`**.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/roles/creer-premier-role
```

## ⚙️ Target tree

```text
labs/roles/creer-premier-role/
├── README.md           ← this file
├── inventory/          ← lab-local inventory
├── playbook.yml        ← TO CREATE: calls the webserver role
├── roles/
│   └── webserver/      ← running-theme role (already created)
│       ├── tasks/main.yml
│       ├── defaults/main.yml
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       └── README.md
└── challenge/
    ├── README.md       ← final challenge
    ├── solution.yml    ← TO CREATE: reproduce the role on db1.lab
    └── tests/
        └── test_webserver.py
```

## 📚 Exercise 1 — Inspect the role structure

```bash
tree roles/webserver/
```

Expected output:

```text
roles/webserver/
├── README.md
├── defaults/
│   └── main.yml
├── files/
├── handlers/
│   └── main.yml
├── meta/
│   └── main.yml
├── tasks/
│   └── main.yml
├── templates/
└── vars/
```

🔍 **Observation**: the structure is identical to what `ansible-galaxy role init webserver` generates. The empty directories (`files/`, `templates/`, `vars/`) are created by `init` even if they contain nothing: a convention to signal that they exist.

## 📚 Exercise 2 — Read `tasks/main.yml`

```bash
cat roles/webserver/tasks/main.yml
```

3 tasks: installation, start, firewall opening. **FQCN everywhere**, idempotence guaranteed by the dedicated modules.

🔍 **Observation to anticipate**: no **variable** in these tasks for now. The role is **rigid**: it necessarily installs nginx with the default config. Lab 59 introduces variables to make the role parameterizable.

## 📚 Exercise 3 — Read `defaults/main.yml`

```bash
cat roles/webserver/defaults/main.yml
```

3 variables with default values. Prefixed by **`webserver_`** (role-name convention to avoid collisions).

🔍 **Observation**: the variables are **not used yet** in `tasks/main.yml`. Lab 59 will wire them in properly.

## 📚 Exercise 4 — Write the root playbook

Create `playbook.yml` at the root of the lab:

```yaml
---
- name: Déployer le rôle webserver
  hosts: web1.lab
  become: true

  roles:
    - role: webserver
```

🔍 **Observation**: no `tasks:` in the playbook, all tasks come from the role. This is the recommended pattern: **thin playbooks, thick roles**.

## 📚 Exercise 5 — Run the playbook

```bash
ansible-playbook playbook.yml
```

Expected output:

```text
PLAY [Déployer le rôle webserver] *********************************

TASK [Gathering Facts] *****************************************
ok: [web1.lab]

TASK [webserver : Installer nginx] *****************************
changed: [web1.lab]

TASK [webserver : Démarrer et activer nginx] *******************
changed: [web1.lab]

TASK [webserver : Ouvrir le service HTTP dans firewalld] *******
changed: [web1.lab]

PLAY RECAP *****************************************************
web1.lab : ok=4 changed=3 unreachable=0 failed=0
```

🔍 **Observation**: the tasks are **prefixed by `webserver :`** in the output, Ansible clearly identifies the executing role. Very useful for debugging a multi-role play.

## 📚 Exercise 6 — Check idempotence

Re-run:

```bash
ansible-playbook playbook.yml
```

Expected output: `changed=0`. All modules are idempotent: replaying changes nothing.

## 📚 Exercise 7 — Test nginx

```bash
curl http://web1.lab/
```

Expected output: nginx's default welcome page (Welcome to nginx).

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

1. Why place variables in `defaults/` rather than in `vars/`?
2. What happens if you change `webserver_state` to `absent` in the playbook (`vars: webserver_state: absent`)?
3. Why is `firewalld:` in the `ansible.posix` collection and not `ansible.builtin`?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to **reproduce the deployment** on `db1.lab`, but by writing the role yourself instead of reusing the one provided here. Automated tests via `pytest+testinfra`:

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **The role is ultra-simple**: no effective variables in the tasks, no templates, no validation. Lab 59 introduces variables.
- **`ansible-galaxy role init webserver`** generates the same structure as what we have here: useful to know for the RHCE.
- **Production pattern**: a `roles/` directory at the repo root, one subdirectory per role. The playbooks in a `playbooks/` directory.
- **Current limitation**: this role works ONLY on RHEL/Alma (because of `dnf`). Lab 59 will explore Debian/Ubuntu portability.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/roles/creer-premier-role/lab.yml
ansible-lint labs/roles/creer-premier-role/challenge/solution.yml
ansible-lint --profile production labs/roles/creer-premier-role/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
