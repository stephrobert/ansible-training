# Lab — Module `filesystem:` (create a filesystem)

> ⚠️ **Destructive lab.** Operates on a **real disk**. Always on a **throwaway VM**.
>
> 💡 **Self-contained lab.** Prerequisite: `ansible-galaxy collection install
> community.general ansible.posix`. The lab's `setup.yaml` partitions the
> secondary disk **`/dev/vdb`** of **db1.lab** into 2: `/dev/vdb1` (1 GiB)
> and `/dev/vdb2` (the rest). Both are well above the **300 MiB**
> that xfs requires.

## 🧠 Recap

🔗 [**Ansible filesystem module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-filesystem/)

`community.general.filesystem:` creates a **filesystem** on a partition or a
logical volume: `ext4`, `xfs`, `btrfs`, `f2fs`, `swap`. It is the step **after
the partition** and **before the mount**.

**Important**: by default the module **never destroys** an existing fs
(protection against data loss). You need `force: true` to force it.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** an ext4 and an xfs fs on 2 partitions.
2. **Choose** the right fstype for the use case.
3. **Understand** the 300 MiB minimum of xfs (verified in the lab).
4. **Force** recreation with `force: true`.

## 🔧 Preparation

The lab's `setup.yaml`, run by `dsoxlab run`, resets `/dev/vdb` then lays down
the 2 working partitions. Check that they are there:

```bash
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

> ⚠️ **xfs refuses filesystems < 300 MiB** (`Filesystem must be larger than
> 300MB`). The partitions laid down by the setup (1 GiB and ~4 GiB) are
> sized to pass without a second thought.

## 📚 Exercise 1 — Create ext4 + xfs

```yaml
---
- name: Demo filesystem
  hosts: db1.lab
  become: true
  tasks:
    - name: Créer ext4
      community.general.filesystem:
        fstype: ext4
        dev: /dev/vdb1
        state: present

    - name: Créer xfs
      community.general.filesystem:
        fstype: xfs
        dev: /dev/vdb2
        state: present
```

Run it twice and check idempotence (2nd run = `ok`).
Check: `blkid /dev/vdb1 /dev/vdb2` returns `TYPE="ext4"` and `TYPE="xfs"`.

> 💡 This lab's **challenge** asks for a **swap** on `/dev/vdb1`, not an
> ext4: this exercise is meant to see the module at work on 2 fstypes.

## 📚 Exercise 2 — Protection against destruction

Try to change the fstype without `force`:

```yaml
- community.general.filesystem:
    fstype: xfs       # while vdb1 is ext4
    dev: /dev/vdb1
```

**Observe**: task **`failed`**, the module refuses to overwrite an existing fs.

To force it (data loss accepted):

```yaml
- community.general.filesystem:
    fstype: xfs
    dev: /dev/vdb1
    force: true
```

## 🔍 Observations to note

- **Idempotence**: a second run of the playbook must show `changed=0` on
  all tasks of the `community.general.filesystem` module. If a task stays `changed=1`, the
  regex/condition is not anchored correctly (see the exercises).
- **Explicit FQCN**: `community.general.filesystem` (not its short name), checked by `ansible-lint
  --profile production`.
- **`validate:`** when available (lineinfile, copy, template): an external
  binary checks the file syntax before writing, which avoids breaking a
  service with an invalid config.
- **Targeting convention**: this lab targets **db1.lab** (a single host to
  isolate the destructive impact).

## 🤔 Reflection questions

1. When should you use `community.general.filesystem` rather than `command: mkfs.<fstype>` (not idempotent, you must test whether it is already formatted)? List 2 cases where each
   alternative would be preferable (readability, idempotence, performance).

2. If you had to create a filesystem (ext4, xfs, swap) on a block device across **50 servers in parallel**, which
   Ansible parameters (`forks`, `serial`, `strategy`) would you tune to
   meet a 5-minute SLA?

3. How do you handle the case where the module fails **partially** (success on
   some tasks, failure on others)? Which strategies let you resume without
   replaying everything (`block/rescue`, `--start-at-task`, a state
   marker)?

## 🚀 Final challenge

Once you have digested the exercises above, launch the **self-contained challenge**:

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-rhel/filesystem --challenge
# or
cat labs/modules-rhel/filesystem/challenge/README.md
```

The challenge asks you to write your `challenge/solution.yml` without looking
at the exercises. Validation with `pytest`:

```bash
pytest -v labs/modules-rhel/filesystem/challenge/tests/
```

## 💡 Going further

- Combine `community.general.filesystem` with **`backup: true`** to keep a
  timestamped copy of the original file before modification, useful for rollback.
- Study **`check_mode: true`** + `--diff`: Ansible shows you what it
  would do without applying anything. Essential in production.
- Compare the **performance** between 1 `community.general.filesystem` task × 10 and 1 task
  `template:` that generates the whole file at once: the
  template is often faster AND more readable as the number of changes grows.

## 🧹 Cleanup

```bash
`dsoxlab clean <id-du-lab>`
```

## 📂 Solution

See `solution/modules-rhel/filesystem/solution.yml` (verified on the real
secondary disk `/dev/vdb`, AlmaLinux 9, ansible-core 2.18,
community.general 12.x).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-rhel/filesystem/lab.yml
ansible-lint labs/modules-rhel/filesystem/challenge/solution.yml
ansible-lint --profile production labs/modules-rhel/filesystem/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows the RHCE 2026 best practices.
