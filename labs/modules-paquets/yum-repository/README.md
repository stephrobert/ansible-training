# Lab — `yum_repository:` module (declaring an RPM repository)

> 💡 **Self-contained lab.** Prerequisite: RHEL/AlmaLinux/Rocky VM available and `ansible-galaxy collection install ansible.posix`.

## 🧠 Recap

🔗 [**Ansible yum_repository module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-yum-repository/)

`ansible.builtin.yum_repository:` declares an **RPM repository** (yum/dnf) by
generating the `.repo` file in `/etc/yum.repos.d/`. It is the tool to
**enable EPEL**, add the **Docker CE** repo, declare an **internal
repo**, or disable a default repo.

**Typical chain**: `rpm_key:` (imports the GPG key) →
`yum_repository:` (declares the repo) → `dnf:` (installs the packages).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Import** a GPG key with `rpm_key:`.
2. **Declare** a repo with `yum_repository:` (gpgcheck mandatory).
3. **Disable** a repo without removing it (`enabled: false`).
4. **Distinguish** `yum_repository:` (declares a repo) from `dnf:` (installs).
5. Understand the **macros** `$releasever`, `$basearch`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping        # assume an AlmaLinux/Rocky VM
```

## 📚 Exercise 1 — Enable EPEL 9

```yaml
---
- name: Activer EPEL 9
  hosts: db1.lab    # ideally an AlmaLinux 9 or Rocky 9 VM
  become: true
  tasks:
    - name: Importer la clé GPG EPEL 9
      ansible.builtin.rpm_key:
        state: present
        key: https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-9

    - name: Déclarer le dépôt EPEL 9
      ansible.builtin.yum_repository:
        name: epel
        description: "Extra Packages for Enterprise Linux 9"
        baseurl: "https://dl.fedoraproject.org/pub/epel/9/Everything/$basearch/"
        gpgcheck: true
        gpgkey: https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-9
        enabled: true
        state: present

    - name: Tester — installer un paquet d'EPEL
      ansible.builtin.dnf:
        name: htop
        state: present
```

Run it twice: 2nd run `ok` (idempotent).

## 📚 Exercise 2 — Disable a repo without removing it

```yaml
- name: Désactiver le dépôt epel sans supprimer le fichier
  ansible.builtin.yum_repository:
    name: epel
    description: "EPEL — désactivé par stratégie"
    file: epel
    enabled: false
    state: present
```

**Verify**: `dnf repolist all | grep epel` shows `disabled`.

## 📚 Exercise 3 — Local repo without GPG (for testing, NEVER in prod)

```yaml
- ansible.builtin.yum_repository:
    name: local-test
    description: "Dépôt local de test"
    baseurl: "file:///srv/repo/"
    gpgcheck: false   # lab only
```

**Read the doc on security**: `gpgcheck: false` is a vulnerability in production.

## 🔍 Observations to note

- **Idempotence**: a second run of the playbook must show `changed=0` on
  all the tasks of the `ansible.builtin.yum_repository` module. If a task stays `changed=1`, it means
  the regex/condition is not anchored correctly (see exercises).
- **Explicit FQCN**: `ansible.builtin.yum_repository` (not its short name): `ansible-lint
  --profile production` checks it.
- **`validate:`** when available (lineinfile, copy, template): an
  external binary checks the file syntax before writing, which avoids
  breaking a service with an invalid config.
- **Targeting convention**: this lab targets **db1.lab** (a single host to
  isolate the destructive impact).

## 🤔 Reflection questions

1. When to use `ansible.builtin.yum_repository` rather than manual manipulation of `/etc/yum.repos.d/*.repo` via `copy:` (less idempotent)? List 2 cases where each
   alternative would be preferable (readability, idempotence, performance).

2. If you had to declare or disable an RPM repo on **50 servers in parallel**, which
   Ansible parameters (`forks`, `serial`, `strategy`) would you tune to
   hold a 5-minute SLA?

3. How to handle the case where the module fails **partially** (success on
   some tasks, failure on others)? Which strategies let you
   resume without replaying everything (`block/rescue`, `--start-at-task`, state
   marker)?

## 🚀 Final challenge

Once the above exercises are digested, launch the **standalone challenge**:

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-paquets/yum-repository --challenge
# or
cat labs/modules-paquets/yum-repository/challenge/README.md
```

The challenge asks you to write your `challenge/solution.yml` without looking
at the exercises. Validation with `pytest`:

```bash
pytest -v labs/modules-paquets/yum-repository/challenge/tests/
```

## 💡 Going further

- Combine `ansible.builtin.yum_repository` with **`backup: true`** to keep a timestamped
  copy of the original file before modification: useful for rollback.
- Study **`check_mode: true`** + `--diff`: Ansible shows you what it
  would do without applying anything. Essential in production.
- Compare the **performance** between 1 `ansible.builtin.yum_repository` task × 10 and 1
  `template:` task that generates the complete file in one go: often the
  template is faster AND more readable when the number of changes grows.

## 🧹 Cleanup

```bash
`dsoxlab clean <id-du-lab>`
```

## 📂 Solution

See `solution/modules-paquets/yum-repository/solution.yml`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-paquets/yum-repository/lab.yml
ansible-lint labs/modules-paquets/yum-repository/challenge/solution.yml
ansible-lint --profile production labs/modules-paquets/yum-repository/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows RHCE 2026 best practices.
