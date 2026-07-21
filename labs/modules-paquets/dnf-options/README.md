# Lab 37 — `dnf:` module: RHEL-specific options

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

🔗 [**Ansible dnf module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-dnf-options/)

On a 100% RHEL/RockyLinux/AlmaLinux fleet, **`dnf:` is more powerful than
`package:`** because it exposes the **DNF-specific** options:

- **`enablerepo:`** / **`disablerepo:`**: enable / disable a repo for the
  duration of an operation.
- **`security: true`** / **`bugfix: true`**: limit to security or bugfix
  **errata**.
- **`exclude:`**: exclude packages (wildcard patterns).
- **`autoremove: true`**: clean up orphaned dependencies.
- **`update_cache: true`**: force a refresh of the repo metadata.
- **`download_only: true`**: pre-download without installing.

These options are **explicit for RHCE 2026**: you will be tested on
**security patching** (`security: true`) and temporary repo enablement.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Enable a repo temporarily** with `enablerepo:` (without persisting it).
2. **Patch only the CVEs** with `security: true`.
3. **Exclude the kernel** from a mass upgrade (`exclude: kernel*`).
4. **Clean up** orphaned dependencies with `autoremove: true`.
5. **Pre-download** RPMs with `download_only: true` for an air-gapped
   upgrade.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "dnf -y remove htop ncdu epel-release 2>/dev/null; true"
```

## 📚 Exercise 1 — `enablerepo: epel` (enable EPEL temporarily)

EPEL (Extra Packages for Enterprise Linux) contains `htop`, `ncdu`, `iftop`, etc.
which are not in the base RHEL repos.

```yaml
---
- name: Demo dnf enablerepo
  hosts: db1.lab
  become: true
  tasks:
    - name: Installer epel-release (la conf du repo EPEL)
      ansible.builtin.dnf:
        name: epel-release
        state: present

    - name: Installer htop depuis EPEL (sans persister l activation)
      ansible.builtin.dnf:
        name: htop
        state: present
        enablerepo: epel

    - name: Verifier que htop est dispo
      ansible.builtin.command: htop --version
      register: htop_version
      changed_when: false

    - name: Afficher la version
      ansible.builtin.debug:
        msg: "{{ htop_version.stdout }}"
```

**Run**:

```bash
ansible-playbook labs/modules-paquets/dnf-options/lab.yml
```

🔍 **Observation**: `htop` is installed via EPEL. **`enablerepo:`** enables EPEL
**only for this task**: no persistent modification. On the next
`dnf list`, EPEL will be **disabled** by default. Useful when you do **not
want to expose EPEL to automatic updates** (packages not always stable).

## 📚 Exercise 2 — `security: true` (patch only the CVEs)

This is **the most useful pattern** in production. Applies **only** the
errata classified as "Security Advisory" by the RHEL vendor.

```yaml
- name: Patcher uniquement les CVE
  ansible.builtin.dnf:
    name: '*'
    state: latest
    security: true
```

🔍 **Observation**:

- **`name: '*'`** = all installed packages.
- **`state: latest`** = update.
- **`security: true`** = **filter**: only the packages with a security
  errata available.

**Consequence**: out of 1000 installed packages, maybe 5-10 have a security
patch available: only those are touched. The others stay at their
current version.

**Combine with `bugfix: true`** for bugfixes:

```yaml
- name: Patcher securite ET bugs
  ansible.builtin.dnf:
    name: '*'
    state: latest
    security: true
    bugfix: true
```

## 📚 Exercise 3 — `exclude: kernel*` (preserve sensitive packages)

```yaml
- name: Mise a jour complete sauf kernel
  ansible.builtin.dnf:
    name: '*'
    state: latest
    exclude: kernel*
```

🔍 **Observation**: a kernel upgrade **requires a reboot**. If you apply
the security patches **without a scheduled reboot**, `exclude: kernel*` avoids
putting the machine in a "kernel staged but not running" state (degraded
security until the next reboot).

**`exclude:` accepts a list**:

```yaml
exclude:
  - kernel*
  - glibc
  - systemd
```

**Wildcards**: `kernel*` matches `kernel`, `kernel-headers`, `kernel-modules`,
`kernel-tools`, etc.

## 📚 Exercise 4 — `autoremove: true` (clean up orphans)

```yaml
- name: Installer un paquet avec dependances
  ansible.builtin.dnf:
    name: nginx
    state: present

- name: Desinstaller nginx ET ses dependances orphelines
  ansible.builtin.dnf:
    name: nginx
    state: absent
    autoremove: true
```

🔍 **Observation**: when you uninstall `nginx`, its exclusive dependencies
(`nginx-core`, `nginx-filesystem`, `almalinux-logos-httpd`) become
**orphaned**. **`autoremove: true`** removes them automatically, like
`dnf autoremove` after a `dnf remove`.

**Without `autoremove`**, you accumulate ghost packages over the
install/uninstall cycles. On a long-living system, that can represent 100+
useless packages.

## 📚 Exercise 5 — `update_cache: true` (refresh repos)

```yaml
- name: Refresh cache puis installer
  ansible.builtin.dnf:
    name: nginx
    state: latest
    update_cache: true
```

🔍 **Observation**: by default, DNF uses a **metadata cache** (TTL ~6h).
**`update_cache: true`** forces an **immediate refresh**: useful when you have
just:

- Modified a `.repo` file (new repo added).
- Pushed a new package into an **internal repo**.
- Enabled a new channel.

**Cost**: the refresh takes 5-30s depending on the repos (CDN, network). Put it
**once** at the start of the play, not per task.

## 📚 Exercise 6 — `download_only: true` (pre-stage)

```yaml
- name: Pre-telecharger pour install offline
  ansible.builtin.dnf:
    name:
      - bind
      - dhcp-server
    state: present
    download_only: true
    download_dir: /var/cache/staged-rpms/
```

🔍 **Observation**: Ansible downloads the RPMs into `download_dir` **without
installing them**. Pattern used to:

- **Prepare an air-gapped upgrade**: download on a connected node, push
  onto an isolated node via `copy:`.
- **Reduce the outage window**: pre-stage 2h before maintenance, install
  in 30s during the window.

## 📚 Exercise 7 — The trap: `state: absent` + shared dependency

```yaml
- name: Desinstaller bind sans autoremove
  ansible.builtin.dnf:
    name: bind
    state: absent
    autoremove: true
```

🔍 **Observation**: `bind` depends on `bind-libs` which is **also used** by
other packages (`bind-utils`, sometimes `glibc`). `autoremove: true` can
**remove too much** if DNF considers the dependency orphaned.

**Defensive pattern**: test in `--check` first, or use
`autoremove: false` to leave the dependencies untouched.

```bash
ansible-playbook labs/modules-paquets/dnf-options/lab.yml --check
# Check what would be uninstalled before running for real
```

## 🔍 Observations to note

- **`enablerepo:`** = **temporary** enablement of a repo (without persistent
  modification).
- **`security: true`** = **production patching** pattern (CVE errata
  only).
- **`exclude: kernel*`** = avoid staging a kernel without a scheduled reboot.
- **`autoremove: true`** on `state: absent` = cleanup of orphaned
  dependencies (but can be too aggressive).
- **`update_cache: true`** = force refresh, put it **once** at the start of the
  play.
- **`download_only: true`** = pre-stage for air-gapped upgrades or short
  maintenance.

## 🤔 Reflection questions

1. You want to patch 50 servers with **only the critical CVEs** without
   rebooting. Which complete `dnf:` (combination of `security`, `exclude`, `state`)?

2. `autoremove: true` can be dangerous. Which defensive pattern (combination
   `--check`, `register`, `assert`) to avoid an unexpected removal?

3. What concrete difference between `state: latest` (without `security:`) and
   `state: latest + security: true`? Give an example where it changes the list
   of touched packages.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`name: '@web-server'`**: installation of DNF **groups** (`@base`,
  `@minimal-environment`, `@web-server`). Handy to provision a business
  role without listing 30 packages.
- **`releasever:`**: install a package from a **different major version**
  (e.g. RHEL 9 → RHEL 10). Advanced, reserve for controlled migrations.
- **`config_file:`**: use a custom `dnf.conf` file (different from the
  default). Rare but useful for Docker images.
- **Combination `download_only:` + `copy:`**: complete air-gapped upgrade
  pattern (download on one side, SSH transfer, offline install).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-paquets/dnf-options/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-paquets/dnf-options/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-paquets/dnf-options/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
