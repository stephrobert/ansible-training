# Lab 63 — Molecule: enriched configuration

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Molecule installed (see [lab 62](../introduction/))
> + Podman/Docker available.

## 🧠 Recap

🔗 [**Molecule: advanced configuration**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-installation-config/)

Lab 62 laid down the bare minimum: `molecule.yml`, `converge.yml`, `verify.yml`.
In production, you enrich it with:

| File | Role |
| --- | --- |
| `prepare.yml` | Prepare the instance (prerequisite packages, system services) before `converge` |
| `requirements.yml` | Galaxy collections + roles to install in the test environment |
| `cleanup.yml` | Specific cleanup before `destroy` |
| `side_effect.yml` | "Disruptive" tasks (down a service, edit config) between `converge` and `verify` |

And in `molecule.yml`, you configure:

- **`provisioner.inventory.host_vars`**: per-instance variables.
- **`scenario.test_sequence`**: order of the cycle steps (add `idempotence`).
- **`provisioner.config_options.defaults.callback_enabled`**: Ansible
  callbacks (`profile_tasks`, `timer`).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Add a `prepare.yml` that pre-conditions the instance.
2. Add a `requirements.yml` that declares the dependencies.
3. Configure `host_vars` in `molecule.yml` to customize each instance.
4. Define a custom `test_sequence` including `idempotence`.
5. Enable `profile_tasks` callbacks (perf).

## 🔧 Preparation

Same prerequisites as lab 62.

## ⚙️ Tree

```text
labs/molecule/installation-config/
├── README.md
├── roles/
│   └── webserver/
└── molecule/
    └── default/
        ├── molecule.yml          ← enriched config
        ├── converge.yml
        ├── verify.yml
        ├── prepare.yml           ← NEW
        └── requirements.yml      ← NEW
```

## 📚 Exercise 1 — `prepare.yml`

The `prepare.yml` runs **before** `converge.yml`. Ideal for:

- Installing packages missing from the image (curl, ca-certificates).
- Enabling repositories (epel-release).
- Pre-configuring SELinux or firewalld.

```yaml
---
- name: Prepare
  hosts: all
  gather_facts: true
  tasks:
    - name: Installer pré-requis pour le rôle webserver
      ansible.builtin.package:
        name:
          - curl
          - ca-certificates
        state: present
```

🔍 **Observation**: `prepare.yml` runs **only once** at the start of the
cycle. If you modify it, re-run `molecule destroy` to start
clean.

## 📚 Exercise 2 — `requirements.yml`

Lists the **collections** and **external roles** your role depends on
for the tests:

```yaml
---
collections:
  - name: ansible.posix
    version: ">=2.0.0"
  - name: community.general
    version: ">=10.0.0"

roles:
  - name: geerlingguy.firewall
    version: 3.5.0
```

Molecule automatically installs these dependencies before `converge`.

🔍 **Observation**: `requirements.yml` is the **equivalent of `requirements.txt`
in Python**. Good practice to pin the versions and guarantee
reproducibility.

## 📚 Exercise 3 — `host_vars` in `molecule.yml`

```yaml
provisioner:
  name: ansible
  inventory:
    host_vars:
      instance:
        webserver_listen_port: 8080
        webserver_index_content: "Test Molecule custom"
```

🔍 **Observation**: lets you test **different configurations** without
touching the role. Very useful for matrix testing.

## 📚 Exercise 4 — Custom `test_sequence`

```yaml
scenario:
  test_sequence:
    - dependency
    - destroy
    - syntax
    - create
    - prepare
    - converge
    - idempotence       # ← ESSENTIAL: 2nd run = changed=0
    - verify
    - destroy
```

🔍 **Observation**: `idempotence` is **optional by default**. **Always**
add it: it is what forces the quality of the role.

## 📚 Exercise 5 — `profile_tasks` callbacks

Add in `molecule.yml`:

```yaml
provisioner:
  config_options:
    defaults:
      callback_enabled: profile_tasks, timer
```

🔍 **Observation**: at the end of `converge`, you see **the time of
each task** ranked by duration. Precious to optimize a slow role.

## 🔍 Observations to note

- **`prepare.yml`** is the right place for "infrastructure" prerequisites
  that are not part of the tested role.
- **`requirements.yml`** = reproducibility. Always pin the versions.
- **Molecule `host_vars`** = easy matrix testing without modifying the role.
- **`idempotence` in `test_sequence`** = non-negotiable quality.
- **`profile_tasks`** = free profiling, to enable when debugging.

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

- **Multi-scenarios**: `molecule/default/`, `molecule/cluster/`,
  `molecule/upgrade/` to test different cases. Run a specific
  scenario: `molecule test -s cluster`.
- **`side_effect.yml`**: between `converge` and `verify`, simulate a failure
  (stop service, delete file) to test the recovery role.
- **`MOLECULE_DISTRO`** env var: reuse a single `molecule.yml` to
  test several OSes via CI matrix (lab 65 + 69).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/molecule/installation-config/
```
