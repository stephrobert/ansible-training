# Lab — Module `parted:` (create a disk partition)

> ⚠️ **Destructive lab.** Operates on a **real disk**. Always use
> a **throwaway VM** or a **blank disk**. A wrong unit = lost
> data.
>
> 💡 **Self-contained lab.** Prerequisite: `ansible-galaxy collection install
> community.general`. The secondary disk **`/dev/vdb`** (5 GiB) of
> **db1.lab** is provisioned by the lab infra.

## 🧠 Recap

🔗 [**Ansible parted module**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/module-parted/)

`community.general.parted:` creates, deletes, and inspects Linux **disk
partitions** (MBR or GPT) idempotently. It is the **raw prerequisite** before
any `filesystem:` or `lvg:`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** an aligned primary partition on a blank disk.
2. **Choose** between **MBR** and **GPT** depending on the context.
3. **Combine** several partitions without overlap.
4. Set **flags** (`lvm`, `boot`, `esp`).
5. **Inspect** the existing partition table.

## 🔧 Preparation

**db1.lab** has a **real secondary disk** of 5 GiB, `/dev/vdb`,
provisioned by the lab infra (`extra_disk_gb` in the repo's `meta.yml`):

```bash
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

`dsoxlab run` runs the lab's `setup.yaml`, which makes `/dev/vdb` blank (no
partition, no filesystem signature, no leftover fstab entry).
If you chain from the `filesystem` or `lvm-storage` labs, which share
the same VM and the same disk, it is the one that resets the disk.

## 📚 Exercise 1 — Create a GPT partition

```yaml
---
- name: Demo parted — partition unique
  hosts: db1.lab
  become: true
  tasks:
    - name: Créer une partition GPT de 50 %
      community.general.parted:
        device: /dev/vdb
        number: 1
        state: present
        label: gpt
        part_start: "0%"
        part_end: "50%"
        name: "data"
```

**Check**: `lsblk /dev/vdb` shows `vdb1`, `parted -s /dev/vdb print` shows
`Partition Table: gpt`.

## 📚 Exercise 2 — Several partitions without flags

```yaml
- name: Partition 2 — reste du disque
  community.general.parted:
    device: /dev/vdb
    number: 2
    state: present
    part_start: "50%"
    part_end: "100%"
    name: "lvm"
```

## 📚 Exercise 3 — Inspect without modifying

```yaml
- name: Inspecter /dev/vdb
  community.general.parted:
    device: /dev/vdb
  register: vdb_info

- ansible.builtin.debug:
    msg: "{{ vdb_info.partitions }}"
```

## ⚠️ Note on flags

On **GPT**, the valid flags are `boot`, `bios_grub`, `esp`, `lvm`, `raid`,
`legacy_boot`, etc. On **MBR**, they are `boot`, `lba`, `lvm`, etc. The `boot`
flag on GPT can flip the table to MBR: **prefer `esp`** for
the EFI System Partition, and `lvm` for LVM PVs.

## 🔍 Observations to note

- **Idempotence**: a second run of the playbook must show `changed=0` on
  all tasks of the `community.general.parted` module. If a task stays `changed=1`, the
  regex/condition is not anchored correctly (see the exercises).
- **Explicit FQCN**: `community.general.parted` (not its short name), checked by `ansible-lint
  --profile production`.
- **`validate:`** when available (lineinfile, copy, template): an external
  binary checks the file syntax before writing, which avoids breaking a
  service with an invalid config.
- **Targeting convention**: this lab targets **db1.lab** (a single host to
  isolate the destructive impact).

## 🤔 Reflection questions

1. When should you use `community.general.parted` rather than `command: parted ...` (not idempotent, would recreate on every run)? List 2 cases where each
   alternative would be preferable (readability, idempotence, performance).

2. If you had to partition a disk (GPT/MSDOS, flags, size) across **50 servers in parallel**, which
   Ansible parameters (`forks`, `serial`, `strategy`) would you tune to
   meet a 5-minute SLA?

3. How do you handle the case where the module fails **partially** (success on
   some tasks, failure on others)? Which strategies let you resume without
   replaying everything (`block/rescue`, `--start-at-task`, a state
   marker)?

## 🚀 Final challenge

Once you have digested the exercises above, launch the **self-contained challenge**:

```bash
$ANSIBLE_TRAINING/bin/dsoxlab lab modules-rhel/parted --challenge
# or
cat labs/modules-rhel/parted/challenge/README.md
```

The challenge asks you to write your `challenge/solution.yml` without looking
at the exercises. Validation with `pytest`:

```bash
pytest -v labs/modules-rhel/parted/challenge/tests/
```

## 💡 Going further

- Combine `community.general.parted` with **`backup: true`** to keep a
  timestamped copy of the original file before modification, useful for rollback.
- Study **`check_mode: true`** + `--diff`: Ansible shows you what it
  would do without applying anything. Essential in production.
- Compare the **performance** between 1 `community.general.parted` task × 10 and 1 task
  `template:` that generates the whole file at once: the
  template is often faster AND more readable as the number of changes grows.

## 🧹 Cleanup

```bash
`dsoxlab clean <id-du-lab>`
```

⚠️ The cleanup **destroys** the partition table of `/dev/vdb`.

## 📂 Solution

See `solution/modules-rhel/parted/solution.yml` (verified on the real
secondary disk `/dev/vdb`).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/modules-rhel/parted/lab.yml
ansible-lint labs/modules-rhel/parted/challenge/solution.yml
ansible-lint --profile production labs/modules-rhel/parted/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows the RHCE 2026 best practices.
