# Lab 64 — Molecule: full TDD cycle

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Molecule installed (see [lab 62](../introduction/)).

## 🧠 Recap

🔗 [**TDD cycle with Molecule**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-tdd-cycle/)

**TDD (Test-Driven Development)** applied to an Ansible role:

```text
1. Write the assertions (verify.yml): RED (the tests fail)
2. Write the role's tasks (tasks/main.yml): minimum to pass
3. molecule test → GREEN (the assertions pass)
4. Refactor (improve the code without breaking the tests)
```

This lab demonstrates the TDD cycle on a **new role `users`** (create
users from a list of dicts).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Start a role from the **tests** (`verify.yml`).
2. Write an `argument_specs.yml` that **precedes** the code.
3. Iterate: write the minimal task → `molecule converge` → adjust.
4. Refactor while keeping the tests green.

## 🔧 Preparation

Same prerequisites as lab 62 (Molecule + Podman).

## ⚙️ Tree

```text
labs/molecule/tdd-cycle/
├── README.md
├── roles/
│   └── users/                            ← NEW role (created in TDD)
│       ├── tasks/main.yml                ← iterates over users_to_create
│       ├── defaults/main.yml             ← users_to_create by default
│       └── meta/
│           ├── main.yml
│           └── argument_specs.yml        ← defines users_to_create (list of dicts)
└── molecule/
    └── default/
        ├── molecule.yml
        ├── converge.yml                  ← passes custom users_to_create (with alice/zsh)
        └── verify.yml                    ← ≥4 assertions (TDD cycle)
```

## 📚 Exercise 1 — `verify.yml` first (RED step)

```yaml
---
- name: Verify users role
  hosts: all
  become: true
  tasks:
    - name: Vérifier qu'alice existe
      ansible.builtin.getent:
        database: passwd
        key: alice
    - ansible.builtin.assert:
        that:
          - getent_passwd['alice'] is defined
        fail_msg: "alice n'existe pas"

    - name: Vérifier que le shell d'alice est /bin/zsh
      ansible.builtin.assert:
        that:
          - getent_passwd['alice'][5] == '/bin/zsh'
        fail_msg: "alice n'a pas /bin/zsh"

    # ... at least 2 more assertions ...
```

🔍 **Observation**: you start by **listing the expected behaviors**
as assertions. Without the role, these assertions fail.

## 📚 Exercise 2 — `argument_specs.yml`

Before coding, you declare the role's input contract:

```yaml
argument_specs:
  main:
    options:
      users_to_create:
        type: list
        elements: dict
        required: true
        description: Liste de dicts avec name + shell + (optionnel) groups
        options:
          name:
            type: str
            required: true
          shell:
            type: str
            default: /bin/bash
          groups:
            type: list
            elements: str
            required: false
```

🔍 **Observation**: this file serves as **executable documentation** and a
**safeguard**. The role will reject any malformed call.

## 📚 Exercise 3 — Minimal `tasks/main.yml` (GREEN step)

Your tests are red? Now write the MINIMUM that makes them
pass: a single `ansible.builtin.user` task looping over
`users_to_create`.

```yaml
---
- name: Créer les utilisateurs
  ansible.builtin.user:
    name: "{{ item.name }}"
    shell: ???        # fallback to users_default_shell (role defaults)
    groups: ???       # optional groups of the item
    append: ???       # do not overwrite the existing groups
    state: present
  loop: ???
  loop_control:
    label: "{{ item.name }}"
```

🔍 **Observation**: a `loop:` over the list, `default(...)` for the
optional fields, and the contract (`argument_specs`, `defaults`) as the
single source of truth.

## 📚 Exercise 4 — Run the full cycle

```bash
cd labs/molecule/tdd-cycle
molecule test
```

Steps:

1. `create`: container launched.
2. `converge`: `users` role applied, alice, bob created.
3. `idempotence`: 2nd run, `changed=0`.
4. `verify`: assertions pass → ✅.

If an assertion fails, it means the role does not (yet) do what
is asked. **TDD cycle**: fix the role, re-run.

## 🔍 Observations to note

- **TDD = write the tests BEFORE the code**. It is counter-intuitive at
  first but makes the role **provably correct**.
- **`argument_specs.yml`** is also a form of test (input
  validation).
- **`loop` + `default(omit)` pattern**: standard for roles that
  accept lists of configs with optional fields.
- **Refactor without fear**: as long as `molecule test` passes, you can
  rewrite the role (rename variables, factor out) safely.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to a
   fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to tune to keep acceptable execution times?

2. Which alternative Ansible modules could you have used to achieve
   the same result? What are their trade-offs (guaranteed idempotence,
   performance, external collection dependency)?

3. If a step of the playbook fails mid-execution, what is the impact
   on the hosts already processed? How do you make the scenario resumable
   (`block/rescue/always`, `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`molecule converge` + editing**: iterate quickly without recreating the
  container each time.
- **`molecule verify` alone**: re-run just the assertions after a
  task change.
- **Mutation testing**: deliberately break a task to check
  that the tests catch it. If a test does not break, an
  assertion is missing.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/molecule/tdd-cycle/roles/users/
```
