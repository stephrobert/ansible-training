# Lab 61 — Roles: `argument_specs` (automatic validation)

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

🔗 [**Ansible argument specs: validate a role's inputs**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/argument-specs/)

Without `argument_specs`, **Ansible does not validate** a role's input
variables. If the user passes `webserver_listen_port: "abcd"` (string instead
of int) or `webserver_state: enabled` (instead of `present`), Ansible
runs the role and **fails late** in an obscure task.

**`argument_specs`** (since Ansible 2.11) **validates the inputs before
execution**: type, allowed choices, required values. The error is
**clear and early**.

| Without argument_specs | With argument_specs |
| --- | --- |
| Late error in an obscure task | Error **before** the 1st task |
| Internal Ansible stack trace | Clear message: *"must be one of: present, absent"* |
| Type silently converted (int → str) | Failure if the type is incorrect |
| Missing variable = silent empty value | Explicit failure if `required: true` |

It is the **quality standard** of a modern Galaxy role. `ansible-lint
--profile production` requires `meta/argument_specs.yml` for published roles.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a `meta/argument_specs.yml` file that documents all a role's
   variables.
2. Define the **type** of a variable (`str`, `int`, `bool`, `list`, `dict`).
3. Restrict the values with **`choices:`** (enumeration).
4. Mark a variable **`required: true`**.
5. Provide a documented **`default` value**.
6. See the automatic **error message** Ansible displays on invalid input.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ansible.builtin.ping
```

## ⚙️ Lab tree

```text
labs/roles/argument-specs/
├── README.md                                ← this file
├── roles/
│   └── webserver/
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       ├── defaults/main.yml
│       ├── meta/
│       │   ├── main.yml                     ← galaxy_info (lab 60)
│       │   └── argument_specs.yml           ← TO STUDY (auto validation)
│       ├── vars/main.yml
│       └── templates/nginx.conf.j2
└── challenge/
    ├── README.md                            ← challenge instructions
    └── tests/
        └── test_argument_specs.py
```

## 📚 Exercise 1 — Read `meta/argument_specs.yml`

Open `roles/webserver/meta/argument_specs.yml`:

```yaml
argument_specs:
  main:
    short_description: "Installer et configurer nginx avec validation"
    description:
      - "Ce rôle installe nginx, le configure via un template, ..."
    author:
      - Stéphane Robert

    options:
      webserver_state:
        type: str
        default: present
        description: État du paquet
        choices:
          - present
          - absent
          - latest

      webserver_listen_port:
        type: int
        default: 80
        description: Port d'écoute HTTP (1-65535)

      webserver_service_enabled:
        type: bool
        default: true
        description: Démarrage automatique du service au boot
```

🔍 **Observation**: each option has at least:

| Field | Role |
| --- | --- |
| `type:` | Expected Python type (`str`, `int`, `bool`, `list`, `dict`, `path`, `raw`) |
| `default:` | Value if not provided. **Must be consistent with `defaults/main.yml`**. |
| `description:` | Documentation for `ansible-doc -t role` |
| `choices:` (optional) | List of allowed values. Refuses any other. |
| `required:` (optional) | If `true`, the absence of the variable fails the play |

**`main:`** is the name of the role's **entry point** (`tasks/main.yml`). If
your role has several entry points (see `import_role/include_role` with
`tasks_from:`), you document each one in parallel in `argument_specs:`.

## 📚 Exercise 2 — Test with a valid value

Create a `playbook.yml` at the root of the lab that uses the role with
**valid values**:

```yaml
---
- name: Test argument_specs avec valeurs valides
  hosts: db1.lab
  become: true
  roles:
    - role: webserver
      vars:
        webserver_listen_port: 8090
        webserver_state: present
        webserver_service_state: started
        webserver_index_content: "Argument specs validés !"
```

Run:

```bash
ansible-playbook labs/roles/argument-specs/playbook.yml
```

🔍 **Observation**: the play runs **without a warning** on the variables.
`argument_specs` validated silently.

## 📚 Exercise 3 — Test with an INVALID value

Change `webserver_state` to `enabled` (which is **not** in `choices`):

```yaml
vars:
  webserver_state: enabled    # ← INVALID
```

Re-run:

```bash
ansible-playbook labs/roles/argument-specs/playbook.yml
```

🔍 **Observation**: expected output (excerpt):

```text
TASK [webserver : Validating arguments against arg spec 'main'] ***
fatal: [db1.lab]: FAILED! => {
  "argument_errors": [
    "value of webserver_state must be one of: present, absent, latest, got: enabled"
  ],
  "msg": "Validation of arguments failed: ..."
}
```

The error is:

- **Early**: before the role's 1st task.
- **Clear**: you know exactly which variable and which values are allowed.
- **Blocking**: the role does not run at all.

## 📚 Exercise 4 — Test an incorrect type

Change `webserver_listen_port` to `"abcd"` (string instead of int):

```yaml
vars:
  webserver_listen_port: "abcd"   # ← INVALID (not an int)
```

🔍 **Observation**:

```text
"argument_errors": [
  "argument 'webserver_listen_port' is of type str and we were unable to convert to int"
]
```

`argument_specs` also validates **type conversions**. A numeric string
(`"8080"`) is converted to int automatically, but a non-numeric
string causes a failure.

## 📚 Exercise 5 — Mark a variable `required: true`

Add a **mandatory** option in `argument_specs.yml`:

```yaml
options:
  webserver_admin_email:
    type: str
    required: true
    description: Email de l'administrateur (obligatoire)
```

Re-run **without defining** `webserver_admin_email`. Output:

```text
"argument_errors": [
  "missing required arguments: webserver_admin_email"
]
```

> 💡 **Best practice**: limit `required: true` to what truly
> has no sensible default. Prefer a `default:` that works in the majority
> of cases.

## 🔍 Observations to note

- **`argument_specs` validates BEFORE execution**: an early and clear error.
- **No argument_specs = late validation** in an obscure task.
- **`type:`** forces a check (and automatic conversion if
  possible). Prefer `int`, `bool`, `list`, `dict` over `str` when relevant.
- **`choices:`** is the weapon against typos (`enabled` vs
  `present`).
- **One file per entry point**: `argument_specs.yml` can document
  several sections (`main:`, `install:`, `configure:` …).
- **`ansible-doc -t role <path>`** displays the doc generated from
  `argument_specs.yml`. It is free as soon as you have filled in this file.
- **`ansible-lint`'s production profile** requires `meta/argument_specs.yml`:
  a role without it is rejected.

## 🤔 Reflection questions

1. You have `defaults/main.yml: webserver_listen_port: 80` but
   `argument_specs.yml: webserver_listen_port: { type: int, default: 8080 }`.
   Which value will be used by default? Why is it a pitfall?

2. You want to accept **any string** for `webserver_index_content`
   but **refuse** empty strings. How do you express it in
   `argument_specs.yml`? (Hint: `required: true`).

3. `argument_specs` does not validate **numeric ranges** (e.g. port between
   1 and 65535). How do you add this validation? (Hint: combine with
   an `assert:` at the start of `tasks/main.yml`.)

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`argument_specs` for `tasks_from:`**: if your role has an alternative
  entry point (`tasks/install.yml`, `tasks/configure.yml`), document them
  in `argument_specs.yml: install:`, `argument_specs.yml: configure:`.
- **Ranges with `assert:`**: at the role's 1st task, add an
  `assert: that: [webserver_listen_port > 0, webserver_listen_port <= 65535]`.
- **`mutually_exclusive`** in a higher version of Ansible: lets
  you declare that 2 options cannot be used together.
- **Automatic doc generation**: `ansible-doc -t role webserver` reads
  `argument_specs.yml` and formats the doc in the CLI.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/roles/argument-specs/roles/webserver/
ansible-lint --profile production labs/roles/argument-specs/
```

The `production` profile validates in particular the **presence** and the **consistency**
of `argument_specs.yml` with `defaults/main.yml`.
