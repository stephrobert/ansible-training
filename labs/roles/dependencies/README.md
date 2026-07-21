# Lab 72 — Dependencies between roles (`meta/main.yml: dependencies:`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Single prerequisite: the 4 lab VMs respond to the ping.

## 🧠 Recap

🔗 [**Dependencies between Ansible roles**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/dependencies/)

A role can **declare** other roles it depends on. Ansible runs
them **before** it.

```yaml
# roles/webserver/meta/main.yml
dependencies:
  - role: selinux_setup
    vars:
      selinux_setup_state: enforcing
  - role: firewall_setup
    vars:
      firewall_setup_open_ports:
        - 80/tcp
        - 443/tcp
```

→ When you run `webserver`, Ansible executes **in this order**:
`selinux_setup` → `firewall_setup` → `webserver`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Declare **`dependencies:`** in `meta/main.yml`.
2. Pass **variables** to the dependent roles.
3. Understand the **execution order** of the dependencies.
4. Avoid the **diamond** pitfall (A depends on B and C, B and C
   depend on D: how many times does D run?).
5. Differentiate `dependencies:` (meta) from `import_role`/`include_role`
   (lab 71).

## 🔧 Preparation

```bash
ansible db1.lab -m ansible.builtin.ping
```

## ⚙️ Tree

```text
labs/roles/dependencies/
├── README.md
├── challenge/
│   └── solution.yml               ← to write: consumes webserver only
└── roles/
    ├── webserver/
    │   ├── meta/main.yml         ← dependencies: [selinux_setup, firewall_setup]
    │   └── tasks/main.yml
    ├── selinux_setup/             ← dependency role #1
    │   ├── meta/main.yml
    │   ├── tasks/main.yml
    │   └── defaults/main.yml
    └── firewall_setup/            ← dependency role #2
        ├── meta/main.yml
        ├── tasks/main.yml
        └── defaults/main.yml
```

## 📚 Exercise 1 — Read `roles/webserver/meta/main.yml`

```yaml
galaxy_info:
  # ... (fields from lab 60) ...

dependencies:
  - role: selinux_setup
    vars:
      selinux_setup_state: enforcing

  - role: firewall_setup
    vars:
      firewall_setup_open_ports:
        - 80/tcp
        - 443/tcp
```

🔍 **Observation**:

- **2 dependencies** declared with their vars.
- **Execution order**: `selinux_setup` → `firewall_setup` → `webserver`.
- The **passed vars** are scoped to the dependency (they do not pollute the
  parent role).

## 📚 Exercise 2 — The `selinux_setup` dependency role

```yaml
# roles/selinux_setup/tasks/main.yml
- name: Tracer l'ordre d'exécution (preuve pour le challenge)
  ansible.builtin.lineinfile:
    path: /tmp/deps-order.txt
    line: selinux_setup
    create: true
    mode: "0644"

- name: S'assurer que SELinux est en mode {{ selinux_setup_state }}
  ansible.posix.selinux:
    policy: targeted
    state: "{{ selinux_setup_state }}"
```

🔍 **Observation**: a "dependency" role has **exactly** the same
structure as a normal role. The only difference: it is referenced
by others in `meta/main.yml`.

## 📚 Exercise 3 — Run the play

Write a minimal play that consumes only the `webserver` role
(see challenge), then:

```bash
ANSIBLE_ROLES_PATH=labs/roles/dependencies/roles \
  ansible-playbook labs/roles/dependencies/challenge/solution.yml
```

🔍 **Expected output**:

```text
TASK [selinux_setup : Tracer l'ordre d'exécution (preuve pour le challenge)]
TASK [selinux_setup : S'assurer que SELinux est en mode enforcing]
TASK [firewall_setup : Tracer l'ordre d'exécution (preuve pour le challenge)]
TASK [firewall_setup : Démarrer et activer firewalld]
TASK [firewall_setup : Ouvrir les ports demandés par l'appelant]
TASK [webserver : Tracer l'ordre d'exécution (preuve pour le challenge)]
TASK [webserver : Installer le paquet nginx]
TASK [webserver : ...]
```

The dependencies are executed **first** (in declaration order),
then the role.

## 📚 Exercise 4 — The diamond pitfall

```text
       myapp
         │
    ┌────┴────┐
    ▼         ▼
selinux    firewall
    │         │
    └────┬────┘
         ▼
       common
```

If `selinux_setup` and `firewall_setup` both depend on `common`,
**how many times does `common` run**?

**Answer**: **only once**. Ansible deduplicates identical dependencies
(same name + same vars).

> ⚠️ **But beware**: if `selinux_setup` calls `common` with
> `vars: {x: 1}` and `firewall_setup` with `vars: {x: 2}`, then `common`
> runs **2 times** (different vars = considered different).

## 📚 Exercise 5 — `dependencies:` vs `include_role:`

| Aspect | `dependencies:` (meta) | `include_role:` (tasks) |
| --- | --- | --- |
| Declaration location | `meta/main.yml` | `tasks/main.yml` |
| Evaluation | Static (at parsing) | Dynamic (runtime) |
| Conditional | No (except via propagated `when:`) | Yes (`when:` at runtime) |
| Visible in `--list-tasks` | No (not explicitly) | Yes |
| Use case | Structural prerequisite **always** applied | Runtime choice based on a variable |

## 🔍 Observations to note

- **`dependencies:`** guarantees that a role has its **structural prerequisites**
  satisfied, **before** its own execution.
- The **vars passed to the dependencies** are scoped: they do not pollute
  the parent role.
- **Automatic deduplication** of identical dependencies (unless
  vars differ).
- **Common pattern**: a `common` role (base users, base packages) that
  almost everything else depends on.

## 🤔 Reflection questions

1. You want `selinux_setup` to run **only on RHEL** (not
   Debian). How do you express it in `dependencies:`? (Hint:
   propagated `when:`.)

2. You have a `common` role that places files, and 3 roles that
   depend on it. On a play that calls the 3 roles, how many times does
   `common` run?

3. When to prefer `dependencies:` over `include_role: + when:`? Give
   a case where one is better than the other.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`allow_duplicates: true`** on the dependency role: allows it to
  run several times (by default, only once).
- **`role_path`**: where Ansible looks for roles (priorities:
  `roles/`, `~/.ansible/roles/`, `/usr/share/ansible/roles/`).
- **Anti-pattern**: do not chain `dependencies:` over 5 levels of
  depth. More readable: a parent play that orchestrates.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/roles/dependencies/
```
