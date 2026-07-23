# Lab 36 — `package:` module (agnostic multi-distro installation)

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

🔗 [**Ansible package module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-package/)

`ansible.builtin.package:` installs packages in an **agnostic** way: Ansible
automatically detects the manager (`ansible_pkg_mgr`) and calls `dnf:` on
RHEL, `apt:` on Debian, `pacman:` on Arch, `zypper:` on SUSE. Ideal for
**multi-distro roles**.

On a 100% RHEL/RockyLinux/AlmaLinux fleet, prefer **`dnf:`** (lab 37) which
exposes specific options (`enablerepo`, `security`, `bugfix`).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Install** one or more packages in a single task.
2. **Distinguish** `state: present` vs `state: latest` (and their risks).
3. **Uninstall** packages for hardening (CIS Benchmark).
4. **Compare** the performance of a **list** vs `loop:` (4× ratio).
5. **Identify** the cases where `package:` is no longer enough (moving to `dnf:`).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "dnf -y remove tree htop ncdu telnet 2>/dev/null; true"
```

## 📚 Exercise 1 — Installing a single package

Create `lab.yml`:

```yaml
---
- name: Demo package simple
  hosts: web1.lab
  become: true
  tasks:
    - name: Installer vim-enhanced
      ansible.builtin.package:
        name: vim-enhanced
        state: present
```

**Run**:

```bash
ansible-playbook labs/modules-paquets/package/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab 'rpm -q vim-enhanced && which vim'
```

🔍 **Observation**:

- First run: `changed=1` (installation).
- Second run: `changed=0` (already installed, idempotent).
- The `vim` binary is in `/usr/bin/` after installation.

## 📚 Exercise 2 — Package list (1 task, N installations)

```yaml
- name: Installer plusieurs paquets en une fois
  ansible.builtin.package:
    name:
      - vim-enhanced
      - bash-completion
      - tree
      - htop
      - ncdu
    state: present
```

**Compare the two approaches** (list vs loop):

```yaml
# A: list (1 dnf call, 5 packages)
- ansible.builtin.package:
    name: [vim-enhanced, bash-completion, tree, htop, ncdu]
    state: present

# B: loop (5 dnf calls, 1 package each)
- ansible.builtin.package:
    name: "{{ item }}"
    state: present
  loop: [vim-enhanced, bash-completion, tree, htop, ncdu]
```

**Run** and compare the durations:

```bash
time ansible-playbook labs/modules-paquets/package/lab.yml
```

🔍 **Observation**: the **list** version is **3-5× faster** than the loop
version. A single `dnf install pkg1 pkg2 pkg3 ...` transaction instead of 5
separate transactions (dependency resolution, yum lock, etc.).

**Rule**: for **independent** packages, **always** the list.

## 📚 Exercise 3 — `state: present` vs `state: latest`

```yaml
- name: present (installe si absent, ne mets PAS a jour)
  ansible.builtin.package:
    name: tree
    state: present

- name: latest (installe ET met a jour vers la derniere version)
  ansible.builtin.package:
    name: tree
    state: latest
```

| `state:` | Behavior | Risk |
|---|---|---|
| `present` (default) | Installs if absent, **does not upgrade** | Low |
| `latest` | Installs **and always upgrades** | **Uncontrolled update** in prod |
| `absent` | Uninstalls if present | Low (idempotent) |

🔍 **Observation**: `state: latest` is **dangerous** on a critical package in
prod: each run can do a silent upgrade. Prefer `state: present` +
**dedicated patching cycle** (`dnf:` with `security: true`).

## 📚 Exercise 4 — Uninstallation for hardening (CIS)

The **CIS Benchmark** requires uninstalling several packages that are dangerous
by default on RHEL.

```yaml
- name: Durcissement CIS - retirer paquets dangereux
  ansible.builtin.package:
    name:
      - telnet
      - rsh
      - ypbind
      - tftp
      - xinetd
    state: absent
```

🔍 **Observation**: `state: absent` is **idempotent**: if the package is not
installed, task `ok`. If installed, clean uninstallation. Pattern
**audit-friendly**: on each run, you check that these packages are indeed absent.

**`telnet`** is target #1: cleartext protocol, the SSH equivalent of the 90s.

## 📚 Exercise 5 — `use:` (force the manager)

By default, Ansible auto-detects (`use: auto`). You can force:

```yaml
- name: Forcer dnf meme si Ansible detecte autre chose
  ansible.builtin.package:
    name: htop
    state: present
    use: dnf
```

🔍 **Observation**: useful on **exotic Docker images** where several
managers coexist (rare but it happens). By default, specify nothing: the
auto-detection works in 99% of cases.

## 📚 Exercise 6 — The trap: package name differs by distro

The `package:` module is agnostic about the **manager**, but **not about the
package names**!

| On RHEL | On Debian |
|---|---|
| `vim-enhanced` | `vim` |
| `httpd` | `apache2` |
| `dnf-utils` | (n/a) |
| `nginx` | `nginx` |
| `mariadb-server` | `mariadb-server` |
| `python3` | `python3` |

The first three lines diverge, the last three do not: that is exactly the
problem, **nothing lets you guess it**, you have to know it or check it.

```yaml
# ❌ Only works on RHEL: on Debian, the package is called "vim"
- ansible.builtin.package:
    name: vim-enhanced
    state: present

# ✅ Multi-distro pattern
- ansible.builtin.package:
    name: "{{ vim_package_name }}"
    state: present
  vars:
    vim_package_name: "{{ 'vim-enhanced' if ansible_os_family == 'RedHat' else 'vim' }}"
```

> 💡 The example uses `vim-enhanced` because it is a package that **this lab
> actually installs**: you can check its name on the VM. The best-known
> textbook case remains `httpd` (RHEL) versus `apache2` (Debian). Conversely,
> `nginx` (this training's web server) has the same name everywhere: the
> divergence is not a rule, it is an occasional trap.

🔍 **Observation**: the module is **multi-distro**, but **you** must handle the
name mapping via `when:`, `vars:`, or `group_vars/<distribution>.yml`.

## 📚 Exercise 7 — When `package:` is no longer enough

`package:` exposes **only the common options**. For these cases, move to `dnf:`
or `apt:` directly:

| Need | Module |
|---|---|
| Enable a repo temporarily | `dnf: enablerepo:` |
| **Security** updates only | `dnf: security: true` |
| Update cache (refresh repos) | `dnf: update_cache:` |
| **Group** installation (`@web-server`) | `dnf: name: '@web-server'` |
| Pre-download without installing | `dnf: download_only:` |

🔍 **Observation**: these options are **specific** to `dnf` (RHEL) or `apt`
(Debian). To use them, drop `package:` in favor of the specific module.

## 🔍 Observations to note

- **`package:`** = multi-distro (auto-detection of the manager).
- **A package list** in `name:` is **3-5× faster** than a loop.
- **`state: latest`** is dangerous in prod: prefer `present` + a patching cycle.
- **`state: absent`** = a **hardening** tool (CIS Benchmark).
- **Package names differ** between distros (`vim-enhanced` vs `vim`, `httpd` vs `apache2`), but not always (`nginx` everywhere).
- **`package:` does not expose** `enablerepo`, `security`, `update_cache`: move to `dnf:` (lab 37).

## 🤔 Reflection questions

1. You write a role for **AlmaLinux + Ubuntu**. What structure to handle
   the different package names? (hint: `vars:` + `ansible_os_family`).

2. A colleague suggests `state: latest` on all packages "to have the
   latest versions". What are the **3 risks** in prod?

3. When to move from `package:` to `dnf:` directly? Give **3 specific
   cases**.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`package_facts:`**: module that returns **all installed packages** on
  the managed node (as a dict). Useful for audit or conditional.
- **`dnf:`** (lab 37): RHEL-specific version with advanced options.
- **`apt:`**: Debian equivalent, options `update_cache`, `cache_valid_time`.
- **`package_install_pre` pattern**: an audit play that collects the missing
  packages before a big deploy, to run only the necessary
  installations.
- **`yum:`**: **legacy** alias of `dnf:`, works but deprecated on RHEL 8+.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-paquets/package/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-paquets/package/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-paquets/package/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
