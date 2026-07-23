# Lab 62 — Molecule: introduction

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: `pipx install molecule molecule-plugins[podman]` (or `[docker]`)
> and **podman/docker** available. No need for the Ansible VMs: Molecule
> tests in local containers.

## 🧠 Recap

🔗 [**Testing an Ansible role with Molecule**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tdd-molecule-introduction/)

**Molecule** is the reference tool for **testing Ansible roles**. It
automates a full cycle:

```text
create → prepare → converge → idempotence → verify → destroy
```

| Step | Effect |
| --- | --- |
| `create` | Creates a container (Podman/Docker) or a VM |
| `prepare` | Installs the prerequisites in the instance |
| `converge` | Applies the role (= `ansible-playbook converge.yml`) |
| `idempotence` | Re-runs to check `changed=0` |
| `verify` | Runs the assertions (verify.yml) |
| `destroy` | Destroys the instance |

**TDD cycle**: you write the `verify.yml` (assertions) **before** writing the
role's tasks. When `verify` passes, the role works.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Understand the tree of a Molecule scenario (`molecule/default/`).
2. Read `molecule.yml`, `converge.yml`, `verify.yml`.
3. Identify the **driver** (Podman, Docker, delegated, default).
4. Identify the test **platforms** (instances to create).
5. Identify the **verifier** (Ansible-assert or testinfra).

## 🔧 Preparation

```bash
pipx install molecule
pipx inject molecule molecule-plugins[podman]
podman --version       # or docker --version
molecule --version
```

## ⚙️ Lab tree

```text
labs/molecule/introduction/
├── README.md
├── roles/
│   └── webserver/                    ← role to test (shipped)
└── molecule/
    └── default/                      ← "default" scenario (shipped)
        ├── molecule.yml              ← Molecule config (driver, platforms, verifier)
        ├── converge.yml              ← play that applies the role
        └── verify.yml                ← post-converge assertions
```

## 📚 Exercise 1 — Read `molecule/default/molecule.yml`

```bash
cat labs/molecule/introduction/molecule/default/molecule.yml
```

🔍 **Observation**: 4 mandatory sections:

```yaml
driver:
  name: podman              # or docker, default, delegated

platforms:
  - name: instance-rhel
    image: quay.io/centos/centos:stream10
    privileged: true
    pre_build_image: true

provisioner:
  name: ansible             # always ansible

verifier:
  name: ansible             # or testinfra
```

## 📚 Exercise 2 — Read `converge.yml`

This is the play that **applies the role** on the created instance:

```yaml
---
- name: Converge - apply webserver role
  hosts: all
  become: true
  roles:
    - role: webserver
```

🔍 **Observation**: `hosts: all` targets **the Molecule instances** (not your
managed nodes from the Ansible lab). Molecule generates its own inventory on
the fly.

## 📚 Exercise 3 — Read `verify.yml`

```yaml
---
- name: Verify
  hosts: all
  become: true
  tasks:
    - name: Vérifier que nginx est installé
      ansible.builtin.package_facts:
    - ansible.builtin.assert:
        that:
          - "'nginx' in ansible_facts.packages"
        fail_msg: "nginx n'est pas installé"

    - name: Vérifier que le service tourne
      ansible.builtin.service_facts:
    - ansible.builtin.assert:
        that:
          - ansible_facts.services['nginx.service'].state == 'running'
```

🔍 **Observation**: verify uses **Ansible assertions** (`verifier: ansible`
mode). You can also use **testinfra** (`verifier: testinfra` mode) which
writes Python tests: covered in lab 66.

## 📚 Exercise 4 — Run Molecule

```bash
cd labs/molecule/introduction
molecule test
```

🔍 **Expected output** (excerpt):

```text
INFO     Running default > create
...
INFO     Running default > converge
TASK [webserver : Installer nginx] *** changed
...
INFO     Running default > idempotence
TASK [webserver : Installer nginx] *** ok    ← changed=0
...
INFO     Running default > verify
TASK [Vérifier que nginx est installé] *** ok
...
INFO     Running default > destroy
```

If everything is green, your role works **and is idempotent**.

## 🔍 Observations to note

- **1 lab = 1 Molecule scenario**: the `default/` scenario is the minimum.
  You can have several (`default/`, `cluster/`, `upgrade/`) to
  test different use cases.
- **Container ≠ VM**: Molecule + Podman tests very fast (~10-30 s) but
  without real systemd by default. To test systemd, you need an image that
  ships it: `pre_build_image: true` + an "init" variant
  (`docker.io/almalinux/10-init`) with `command: /sbin/init` and
  `privileged: true`. Watch out for the trap: a distro's base image
  does NOT have systemd (`docker.io/rockylinux/rockylinux:9` does not even have
  `/sbin/init`), and the role then fails on starting the service.
- **Forced idempotence**: Molecule **fails** if a task stays `changed`
  on the 2nd run. This is an essential safeguard.

## 🤔 Reflection questions

1. You want to test your role on **3 different OSes** (RHEL, Debian,
   Ubuntu). How many platforms do you declare in `molecule.yml`?
   (Hint: lab 65.)

2. The `verify.yml` uses `verifier: ansible`. What is the advantage
   of using `verifier: testinfra` instead? (Hint: lab 66.)

3. You want Molecule to **keep** the instance after `converge` (to
   inspect it manually). Which command do you use instead of
   `molecule test`? (Hint: `molecule converge` + `molecule login`.)

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`molecule converge`** alone: applies without destroy. Useful for debugging.
- **`molecule login`**: opens a shell in the instance.
- **`molecule destroy --all`**: cleans up all scenarios.
- **`MOLECULE_NO_LOG=false`**: maximum verbosity for debugging.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/molecule/introduction/molecule/
ansible-lint --profile production labs/molecule/introduction/
```
