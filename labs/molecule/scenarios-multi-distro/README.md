# Lab 65 — Molecule: multi-distro scenarios

> 💡 **Landing directly on this lab without having done the previous ones?**
> Prerequisite: Molecule + Podman/Docker installed (see [lab 62](../introduction/)).

> **Why AlmaLinux 10 containers while the lab VMs run AlmaLinux 9?** On purpose.
> Molecule exists to validate a role on distributions *other* than the one you
> develop on: testing against the next major release before migrating is exactly
> its job. Do not "align" these images on the VM distribution — that would remove
> the point of the scenario.

## 🧠 Recap

🔗 [**Testing an Ansible role on several distributions**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-scenarios-multi-distro/)

A Galaxy-ready role must work on **several OSes**: RHEL,
AlmaLinux, Rocky, Debian, Ubuntu, sometimes SUSE. Molecule makes this **simple**
by adding platforms in `molecule.yml`.

The **secret of portability**: use **per-OS abstractions** in
the role:

| Item | Multi-OS pattern |
| --- | --- |
| Package module | `ansible.builtin.package:` (not `dnf:` or `apt:`) |
| Package name | `__webserver_package` variable loaded from `ansible_os_family` |
| System user | `__webserver_user` variable (`nginx` on RHEL, `www-data` on Debian) |
| HTML folder | `__webserver_html_dir` variable (`/usr/share/nginx/html` vs `/var/www/html`) |
| Service | `__webserver_service` variable (usually identical) |

These variables live in `vars/<OS>.yml` and are loaded dynamically by
`include_vars` at role startup.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Test a role on **3 different distributions** (RHEL/Alma + Debian + Ubuntu).
2. Dynamically load `vars/{{ ansible_os_family }}.yml`.
3. Use `ansible.builtin.package:` (agnostic).
4. Diverge paths / package names / users between OSes.
5. Check that the **same role** works on the 3 OSes via Molecule.

## 🔧 Preparation

```bash
podman --version  # or docker
molecule --version
```

## ⚙️ Tree

```text
labs/molecule/scenarios-multi-distro/
├── README.md
├── roles/
│   └── webserver/
│       ├── tasks/main.yml          ← shipped MONO-DISTRO: to make portable
│       ├── defaults/main.yml
│       ├── handlers/main.yml
│       ├── meta/main.yml
│       ├── vars/
│       │   ├── RedHat.yml          ← skeleton to complete
│       │   └── Debian.yml          ← skeleton to complete
│       └── templates/nginx.conf.j2
└── molecule/
    └── default/
        ├── molecule.yml            ← 1 platform shipped: matrix to extend
        ├── converge.yml
        └── verify.yml
```

## 📚 Exercise 1 — `vars/RedHat.yml` vs `vars/Debian.yml`

```yaml
# vars/RedHat.yml (structure example)
__webserver_package_name: nginx
__webserver_user: nginx
__webserver_html_dir: /usr/share/nginx/html
__webserver_service_name: nginx
```

It is up to you to derive `vars/Debian.yml`: same structure, but which
user runs nginx on Debian? Which directory serves the
default pages? (A Debian container and `apt show nginx` answer
in 2 minutes.)

🔍 **Observation**: the `__var_name` convention (double underscore prefix)
indicates a **role-internal** variable, do not override it on the
user side.

## 📚 Exercise 2 — `tasks/main.yml` with dynamic `include_vars`

```yaml
---
- name: Charger les variables OS-specific
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"

- name: Installer le paquet (agnostique)
  ansible.builtin.package:
    name: "{{ __webserver_package }}"
    state: present

- name: Déployer la page d'accueil dans le bon dossier
  ansible.builtin.copy:
    dest: "{{ __webserver_html_dir }}/index.html"
    content: "Hello from {{ ansible_distribution }}\n"
    mode: "0644"
    owner: "{{ __webserver_user }}"
```

🔍 **Observation**:

- `ansible.builtin.package:` picks `dnf`/`apt`/`zypper` depending on the OS.
- `{{ ansible_os_family }}` is `RedHat` or `Debian`: exact match with
  the `vars/` files.
- `include_vars` (dynamic) > `vars_files` (static) because the latter does not work
  in a role.

## 📚 Exercise 3 — `molecule.yml` with 3 platforms

```yaml
platforms:
  - name: instance-rhel
    image: quay.io/centos/centos:stream10
    pre_build_image: true

  - name: instance-debian
    image: docker.io/library/debian:12
    pre_build_image: true

  - name: instance-ubuntu
    image: docker.io/library/ubuntu:24.04
    pre_build_image: true
```

🔍 **Observation**: Molecule creates **3 containers in parallel**, applies
the role, verifies on each. If one of the 3 fails, the whole test fails.

## 📚 Exercise 4 — Run

```bash
cd labs/molecule/scenarios-multi-distro
molecule test
```

🔍 You see 3 instances `converge` in parallel, each distro with its own
path/user/package. The output lists the 3 instances in the PLAY
RECAP.

## 🔍 Observations to note

- **`package:` module** is the main multi-OS weapon. Prefer it over
  `dnf:`/`apt:` unless you need specific options.
- **`vars/<OS_family>.yml`** + `include_vars` = standard pattern. Works
  even for very different OSes.
- **3+ platforms** in `molecule.yml` = a real test matrix.
- **`__var` convention**: role-internal variables. Do **not** put them
  in `defaults/` (which the user can override): put them in `vars/`.

## 🤔 Reflection questions

1. You want to add **SUSE** (`opensuse/leap`) to the matrix. What is
   the value of `ansible_os_family` for SUSE? Which `vars/<OS>.yml`
   should you create?

2. On Debian, the `nginx` service does not start after installation
   (unlike RHEL). How do you force the start **only on
   Debian**?

3. You want to test **2 versions** of AlmaLinux (9 and 10). How many
   platforms in `molecule.yml`? How do you name them to tell them
   apart?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **Ansible `group_by`**: dynamically create groups based on
  `ansible_os_family`, then apply simpler `when:` tasks.
- **`ansible_distribution_major_version`**: distinguish RHEL 9 vs RHEL 10.
- **CI images**: `quay.io/jeffwecan/molecule-rhel:9` and other images
  optimized for Molecule (with systemd).

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile production labs/molecule/scenarios-multi-distro/
```
