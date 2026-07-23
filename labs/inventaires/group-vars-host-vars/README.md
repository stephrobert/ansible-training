# Lab 55 — Structured group_vars and host_vars

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Recap

🔗 [**Ansible inventories: group_vars and host_vars**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/group-vars-host-vars/)

Ansible **automatically** looks for variables in two folders placed **next to the inventory**:

- **`group_vars/<group_name>.yml`**: variables applied to **all the hosts of the group**.
- **`host_vars/<host_name>.yml`**: variables applied to **a single host** (higher priority).

There is also the special group **`all`**: `group_vars/all.yml` is applied to **all the hosts** of the inventory.

**Precedence (from weakest to strongest)**:

```text
1. group_vars/all.yml
2. group_vars/<parent group>.yml
3. group_vars/<child group>.yml
4. host_vars/<host>.yml
```

It is this **precedence** that you will demonstrate in this lab.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Structure a **YAML inventory** with `group_vars/` and `host_vars/` alongside.
2. Define a variable at **3 different levels** (all → group → host).
3. Check the **resolved value** with `ansible-inventory --host <host>`.
4. Demonstrate that the **"most local wins" rule** applies.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/inventaires/group-vars-host-vars
```

## ⚙️ Target tree

```text
labs/inventaires/group-vars-host-vars/
├── README.md           ← this file
├── inventory/
│   ├── hosts.yml       ← YAML inventory
│   ├── group_vars/
│   │   ├── all.yml
│   │   └── webservers.yml
│   └── host_vars/
│       └── web1.lab.yml
└── challenge/
    ├── README.md
    ├── solution.yml
    └── tests/
        └── test_precedence.py
```

## 📚 Exercise 1 — The YAML inventory

Create `inventory/hosts.yml`:

```yaml
---
all:
  children:
    webservers:
      hosts:
        web1.lab:
        web2.lab:
    dbservers:
      hosts:
        db1.lab:
```

🔍 **Observation**: the structure `all.children.<group>.hosts.<host>` is the **standard YAML form**. No need to specify `ansible_host:` if DNS resolution or `/etc/hosts` is correct.

## 📚 Exercise 2 — Variable at the `all` level (low precedence)

Create `inventory/group_vars/all.yml`:

```yaml
---
app_port: 80
```

This value applies to **all the hosts** by default.

## 📚 Exercise 3 — Variable at the level of a group

Create `inventory/group_vars/webservers.yml`:

```yaml
---
app_port: 8080
```

🔍 **Observation**: `app_port` is now **redefined** for the hosts of the `webservers` group. Precedence says that `group_vars/webservers.yml` **wins** over `group_vars/all.yml`.

## 📚 Exercise 4 — Variable at the level of a host

Create `inventory/host_vars/web1.lab.yml`:

```yaml
---
app_port: 9090
```

🔍 **Observation**: for `web1.lab` specifically, `app_port` is **9090**: the most local value wins.

## 📚 Exercise 5 — Check the resolution

```bash
ansible-inventory -i inventory/hosts.yml --host web1.lab
ansible-inventory -i inventory/hosts.yml --host web2.lab
ansible-inventory -i inventory/hosts.yml --host db1.lab
```

**Expected outputs**:

| Host | resolved `app_port` | Source |
|---|---|---|
| `web1.lab` | **9090** | `host_vars/web1.lab.yml` |
| `web2.lab` | **8080** | `group_vars/webservers.yml` |
| `db1.lab` | **80** | `group_vars/all.yml` |

🔍 **Observation**: Ansible automatically merges the variables of the **3 levels** and keeps the **most local** one. This is exactly what you want to configure a fleet with a few pointed exceptions.

## 📚 Exercise 6 — Check the graph

```bash
ansible-inventory -i inventory/hosts.yml --graph
```

**Expected output**:

```text
@all:
  |--@dbservers:
  |  |--db1.lab
  |--@ungrouped:
  |--@webservers:
  |  |--web1.lab
  |  |--web2.lab
```

🔍 **Observation**: `@ungrouped` appears even when empty: this is normal, it is a special group that contains the hosts outside any group.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name: `ansible-lint --profile
  production` checks it.
- **Targeting convention**: this lab targets all (4 VMs); to adapt to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then rerun.
- **Isolated reset**: `dsoxlab clean <lab-id>` at the root of the lab cleanly
  uninstalls what the solution set down so you can replay the scenario.

## 🤔 Reflection questions

1. If you add `app_port: 1234` in the **playbook** (`vars: app_port: 1234`), which value wins on `web1.lab`?

2. How do you **force** a value everywhere, one that cannot be overridden by any group_vars/host_vars? (Hint: `--extra-vars`.)

3. You want to store **an encrypted secret** for `db1.lab`. Where do you place it and with which tool?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to define 3 variables at different levels and to prove their resolution via a playbook that creates marker files on each host. Automated tests via `pytest+testinfra`:

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **`group_vars/<group>/main.yml`**: if a single variable becomes a folder, you can split it (`main.yml`, `vault.yml`, `network.yml`).
- **Full precedence (22 levels)**: see the [dedicated page](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/).
- **Host patterns**: see [lab 56: host patterns](../patterns-hotes/) to target with `--limit`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/inventaires/group-vars-host-vars/lab.yml
ansible-lint labs/inventaires/group-vars-host-vars/challenge/solution.yml
ansible-lint --profile production labs/inventaires/group-vars-host-vars/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
