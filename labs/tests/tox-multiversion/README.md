# Lab 67 — Testing a role on several Ansible versions with `tox`

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisites: `pipx install tox` + Molecule (see [lab 62](../../molecule/introduction/)).

## 🧠 Recap

🔗 [**Testing an Ansible role with multi-version tox**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-tox-multiversion/)

A role distributed on Galaxy must work on **several `ansible-core`
versions** (typically: 2.19, 2.20, 2.21). You can validate this
with **`tox`**, a Python environment orchestrator.

```text
tox.ini
   ├─ envlist = ansible2.{19,20,21}
   ├─ [testenv:ansible2.19] → pin ansible-core==2.19.* → molecule test
   ├─ [testenv:ansible2.20] → pin ansible-core==2.20.* → molecule test
   └─ [testenv:ansible2.21] → pin ansible-core==2.21.* → molecule test
```

`tox` creates 3 isolated venvs, installs the target Ansible version in each,
and runs `molecule test`. If one of the 3 fails, a behavior diverges
between versions: a portability bug is detected.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a `tox.ini` with **several** Ansible **environments**.
2. Pin the `ansible-core` version in each env.
3. Run `tox -e ansible2.21` for a specific version.
4. Run `tox` for **all** versions in parallel.

## 🔧 Preparation

```bash
pipx install tox
tox --version
```

## ⚙️ Tree layout

```text
labs/tests/tox-multiversion/
├── README.md
├── tox.ini             ← multi-version tox config
├── roles/webserver/
└── molecule/default/
```

## 📚 Exercise 1 — Read `tox.ini`

```ini
[tox]
envlist = ansible2.{19,20,21}
skipsdist = true

[testenv]
commands =
    molecule test

[testenv:ansible2.19]
deps =
    ansible-core==2.19.*
    molecule
    molecule-plugins[podman]
    pytest-testinfra

[testenv:ansible2.20]
deps =
    ansible-core==2.20.*
    molecule
    molecule-plugins[podman]
    pytest-testinfra

[testenv:ansible2.21]
deps =
    ansible-core==2.21.*
    molecule
    molecule-plugins[podman]
    pytest-testinfra
```

🔍 **Observation**:

- **`envlist`**: the env names to run by default.
- **`[testenv]`**: config shared by all envs (here the `molecule test` command).
- **`[testenv:ansible2.X]`**: specific config with an Ansible pin.
- **`deps` is repeated in full in each env, on purpose.** You could factor
  the shared lines with `{[testenv]deps}`, but spelling out `ansible-core==2.X.*`
  in every section makes the pinned version readable at a glance, without
  chasing a substitution chain.
- **`ansible-core==2.19.*`** (strict pin on the branch), not `>=2.19,<2.20`:
  a wide range would install the same latest version in all three envs and
  make the matrix decorative. The pin is what the automated tests check.

## 📚 Exercise 2 — Run a specific version

```bash
cd labs/tests/tox-multiversion
tox -e ansible2.21
```

🔍 `tox`:

1. Creates a venv `.tox/ansible2.21/`.
2. Installs `ansible-core==2.21.*` + Molecule + dependencies.
3. Runs `molecule test`.

## 📚 Exercise 3 — All versions

```bash
tox
```

Runs the 3 envs in series. Summary output:

```text
ansible2.19: OK
ansible2.20: OK
ansible2.21: OK
___________ summary ____________
  ansible2.19: commands succeeded
  ansible2.20: commands succeeded
  ansible2.21: commands succeeded
  congratulations :)
```

## 📚 Exercise 4 — Parallelization with `tox-parallel`

```bash
tox -p auto    # parallelizes according to the number of CPUs
```

🔍 Cuts test time by 3x on a 4+ CPU machine.

## 🔍 Observations to note

- **`tox`** is the reference Python tool for testing across several
  dependency versions. Ansible is just one use case.
- **Strict pin** (`==2.21.*`) > wide range (`>=2.19`). You want the CI to
  fail if Ansible publishes a new version you have not validated.
- **Idiomatic** in the Ansible community: every `geerlingguy` role on
  Galaxy has a `tox.ini`.
- **Combinable with a CI matrix** (lab 69-70): GitHub Actions / GitLab can
  run `tox -e ansible-X` in parallel on separate runners.

## 🤔 Reflection questions

1. How would you adapt your solution if the target went from **1 host** to
   a fleet of **50 servers**? Which parameters (`forks`, `serial`, `strategy`)
   would you need to tune to keep execution times acceptable?

2. Which alternative Ansible modules could you have used to reach the same
   result? What are their trade-offs (guaranteed idempotence, performance,
   external collection dependencies)?

3. If a playbook step fails mid-run, what is the impact on the hosts already
   processed? How do you make the scenario resumable
   (`block/rescue/always`, `--start-at-task`, `serial`)?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`tox-ansible`** plugin: automatically generates the envs from
  `meta/main.yml` (`min_ansible_version` fields, etc.).
- **`tox -e lint`**: add an env that only runs `ansible-lint`, separate
  from the Molecule tests.
- **GitHub Actions matrix**: `strategy.matrix.ansible_version: [2.19,
  2.20, 2.21]` → one runner per version, in parallel (lab 69).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/tests/tox-multiversion/
```
