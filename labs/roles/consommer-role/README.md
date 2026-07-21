# Lab 71 — Consume a role: `roles:`, `import_role`, `include_role`

> 💡 **Landing directly on this lab without having done the previous ones?**
> Single prerequisite: the 4 lab VMs respond to the ping (see [root README](../../../README.md#-démarrage-rapide)).

## 🧠 Recap

🔗 [**Consume an Ansible role**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/consommer-role/)

There are **3 ways** to use a role in a play. Choose the right one
according to the need:

| Form | When to use it | Evaluation |
| --- | --- | --- |
| **`roles:`** at play level | Standard case, systematic role | Static |
| **`import_role:`** in `tasks:` | Role conditional on a tag, but evaluated at parsing | Static (tags/when resolved early) |
| **`include_role:`** in `tasks:` | Role conditional on a runtime variable, or loop over N roles | Dynamic (when evaluated at runtime) |

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Use **`roles:`** at play level (standard form).
2. Use **`import_role:`** in `tasks:` (static).
3. Use **`include_role:`** with **`when:`** (dynamic).
4. Choose the right form according to the need (static vs dynamic).
5. Understand why `import_role + when` does **not** behave like
   `include_role + when`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ansible.builtin.ping
```

## ⚙️ Tree

```text
labs/roles/consommer-role/
├── README.md
├── roles/
│   └── webserver/        ← tasks/main.yml (deployment) + tasks/stamp.yml (trace)
└── challenge/
    └── solution.yml      ← to write: the 3 forms, proven on db1.lab
```

## 📚 Exercise 1 — The `roles:` form (the simplest)

```yaml
---
- name: Forme classique avec roles:
  hosts: db1.lab
  become: true

  roles:
    - role: webserver
      vars:
        webserver_listen_port: 8080
```

🔍 **Observation**:

- Always runs (no conditional possible at play level).
- Runs **before** the play's `tasks:` (`pre_tasks` < `roles:` < `tasks:` < `post_tasks:`).
- Variables passed via the role's `vars:`.

## 📚 Exercise 2 — `import_role:` (static)

```yaml
- name: Avec import_role
  hosts: db1.lab
  become: true

  tasks:
    - name: Pre-task
      ansible.builtin.debug:
        msg: "avant le rôle"

    - name: Importer le rôle webserver
      ansible.builtin.import_role:
        name: webserver
      vars:
        webserver_listen_port: 8081
```

🔍 **Observation**:

- Lets you **place** the role in the middle of tasks (not only before).
- **Static**: the role's tasks are expanded at **parsing**. A
  `tags:` set above applies to all the role's tasks. A
  `when:` the same, but **evaluated for each task** (not globally).

## 📚 Exercise 3 — `include_role:` (dynamic)

```yaml
- name: Avec include_role conditionnel
  hosts: db1.lab
  become: true
  vars:
    deploy_webserver: true

  tasks:
    - name: Inclure le rôle webserver SI deploy_webserver=true
      ansible.builtin.include_role:
        name: webserver
      vars:
        webserver_listen_port: 8082
      when: deploy_webserver | bool
```

🔍 **Observation**:

- **Dynamic**: the role is loaded **only if** `when:` is true at
  runtime.
- Lets you **loop** over a list of roles: `loop: [r1, r2, r3]` with
  `include_role: name: "{{ item }}"`.
- Heavier at execution than `import_role` (loading on the fly).

## 📚 Exercise 4 — Compare the behaviors

Write a `lab.yml` reusing the three forms above, then run:

```bash
ANSIBLE_ROLES_PATH=labs/roles/consommer-role/roles \
  ansible-playbook labs/roles/consommer-role/lab.yml --list-tasks
ANSIBLE_ROLES_PATH=labs/roles/consommer-role/roles \
  ansible-playbook labs/roles/consommer-role/lab.yml
```

🔍 **Observation**:

- At **parsing**, `roles:` and `import_role:` are already expanded. You
  see the names of the role's tasks in `--list-tasks`.
- `include_role:` does **not** appear in `--list-tasks`: its content
  is invisible until runtime.

## 🔍 Observations to note

- **`roles:`** = default, the simplest. Use it.
- **`import_role:`** when you want to **place** the role in the middle of
  tasks.
- **`include_role:`** when the role must be **runtime-conditional**
  (extra-vars variable) or a **loop**.
- **`import_role + when:` pitfall**: the `when:` applies to **each
  task** of the role individually, not globally. To not load the role at
  all: `include_role + when:`.

## 🤔 Reflection questions

1. You have 3 roles `webserver`, `database`, `cache`. You want to
   run the one matching `var: app_role`. Which form do you
   use? Why not `roles:`?

2. You have a `firewall` role that you want to tag `firewall` so you
   can filter with `--tags firewall`. `roles:` or `import_role:`?

3. What is the problem with this code?:

   ```yaml
   - import_role:
       name: webserver
     when: ansible_os_family == "RedHat"
   ```

   Spoiler: on Debian, the `when:` is evaluated **per task** of the role, so
   each task is `skipped`, but the role is still **loaded**,
   which can crash on `include_vars` that lack the
   `Debian.yml`. Solution: `include_role + when:`.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`tasks_from:`** on `import_role`/`include_role`: call an
  alternative entry point of the role (e.g. `tasks/configure.yml` instead
  of `tasks/main.yml`).
- **`apply:`** on `include_role`: force `tags:` or a `become:`
  on the inclusion.
- **`public: true`** on `include_role`: make the role's variables
  visible after inclusion (by default they are private).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/roles/consommer-role/challenge/solution.yml
```
