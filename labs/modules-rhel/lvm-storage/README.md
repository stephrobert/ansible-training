# Lab 48 — LVM storage: `lvg:` + `lvol:` + `filesystem:` + `mount:`

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

🔗 [**LVM with Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/systeme/lvm-storage/)

LVM (Logical Volume Manager) abstracts physical disks into **resizable logical
volumes**. Classic pipeline:

1. **PV** (Physical Volume): disk or partition initialized for LVM.
2. **VG** (Volume Group): pool of combined PVs.
3. **LV** (Logical Volume): volume carved out of the VG (the usable "virtual
   disk").

Ansible modules:

- **`community.general.lvg:`**: manage Volume Groups (create/delete,
  add PVs).
- **`community.general.lvol:`**: manage Logical Volumes (create, extend,
  delete).
- **`community.general.filesystem:`**: format an LV or a disk.
- **`ansible.posix.mount:`**: mount and persist in fstab (lab 47).

On RHCE 2026, these 4 modules form the **complete storage pipeline**.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Recognize** the secondary disk dedicated to the storage labs.
2. **Build a PV → VG → LV** chain with the 3 dedicated modules.
3. **Format** an LV as `xfs` or `ext4` with idempotence.
4. **Mount** the LV via `/dev/<vg>/<lv>` in fstab.
5. **Extend** an LV live with `lvol: resizefs: true`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible-galaxy collection install community.general ansible.posix
ansible db1.lab -m ping

# Check the secondary disk dedicated to the storage labs
ansible db1.lab -b -m shell -a "lsblk /dev/vdb"
```

`dsoxlab run` runs the lab's `setup.yaml`, which makes `/dev/vdb` blank (no
partition, no LVM signature, no leftover fstab entry). If you chain
from the `parted` or `filesystem` labs, it is the one that resets the disk.

## 📚 Exercise 1 — Spot the working disk

**db1.lab** has a **real secondary disk** of 5 GiB, `/dev/vdb`,
provisioned by the lab infra (`extra_disk_gb` in the repo's `meta.yml`).
That is the one you hand to LVM, not the system disk.

```yaml
---
- name: Inspecter le disque secondaire
  hosts: db1.lab
  become: true
  tasks:
    - name: Lire la géométrie du disque
      ansible.builtin.command: lsblk /dev/vdb
      register: disk_info
      changed_when: false

    - name: Afficher
      ansible.builtin.debug:
        var: disk_info.stdout_lines
```

🔍 **Observation**: `/dev/vdb` is a 5 GiB block device with no partition. LVM
can work **directly on the whole disk**: unlike a classic
partition, there is no need to go through `parted` first.

## 📚 Exercise 2 — Create the PV + VG (`lvg:`)

```yaml
- name: Creer le Volume Group lab_vg sur le disque secondaire
  community.general.lvg:
    vg: lab_vg
    pvs: /dev/vdb
    state: present
```

🔍 **Observation**: the module does **2 things**:

1. **`pvcreate /dev/vdb`**: initializes the PV.
2. **`vgcreate lab_vg /dev/vdb`**: creates the VG on this PV.

**Idempotent**: 2nd run → `changed=0`.

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo vgdisplay lab_vg | head -10'
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo pvs'
```

**Extend the VG** later with a new disk:

```yaml
- community.general.lvg:
    vg: lab_vg
    pvs: /dev/vdb,/dev/vdc   # Adding the 2nd disk
    state: present
```

## 📚 Exercise 3 — Create the LV (`lvol:`)

```yaml
- name: Creer le Logical Volume lab_lv (1G)
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    size: 1G
    state: present
```

**Format of `size:`**:

- **`100M`**: fixed size.
- **`50%FREE`**: 50% of the VG's free space.
- **`+10G`**: extension by 10 GB (relative).

🔍 **Observation**: the LV is created at `/dev/lab_vg/lab_lv` (or
`/dev/mapper/lab_vg-lab_lv`). Visible in `lsblk`:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo lsblk /dev/vdb'
# vdb               252:16   0     5G  0 disk
# └─lab_vg-lab_lv   253:1    0     1G  0 lvm
```

## 📚 Exercise 4 — Format the LV (`filesystem:`)

```yaml
- name: Formater le LV en xfs
  community.general.filesystem:
    fstype: xfs
    dev: /dev/lab_vg/lab_lv
```

🔍 **Observation**:

- **Idempotent**: if the filesystem is already of the right type, `changed=0`.
- **`force: true`** forces reformatting if another filesystem exists (DANGER:
  data loss).

**Supported filesystems**: `ext2`, `ext3`, `ext4`, `xfs`, `btrfs`, `f2fs`, etc.

**RHCE convention**: **xfs** is the RHEL 7+ default (performant for large
files, snapshots, quotas). **ext4** is still used for `/boot`.

## 📚 Exercise 5 — Mount the LV (`mount:`)

```yaml
- name: Creer le point de montage
  ansible.builtin.file:
    path: /mnt/lvm-data
    state: directory
    mode: "0755"

- name: Monter le LV (via /dev/lab_vg/lab_lv)
  ansible.posix.mount:
    path: /mnt/lvm-data
    src: /dev/lab_vg/lab_lv
    fstype: xfs
    opts: defaults,noatime
    state: mounted
```

🔍 **Observation**:

- `/etc/fstab` now contains a line pointing to `/dev/lab_vg/lab_lv`.
- **Better than using `/dev/vdb`**: LVM manages the **logical alias**, so even
  if the disk changes physical position (`vdb` becomes `vdc` after adding
  hardware), the `/dev/<vg>/<lv>` stays stable.

**Preferred pattern for fstab**: use **`UUID=...`** rather than `/dev/...`:

```yaml
- ansible.posix.mount:
    path: /mnt/lvm-data
    src: "UUID={{ ansible_lvm.lvs.lab_lv.uuid | default('inconnu') }}"
    fstype: xfs
    state: mounted
```

The UUID survives renames, even more stable than LVM.

## 📚 Exercise 6 — Extend an LV live (`resizefs: true`)

Real case: your `/var/log/` is full. You extend the LV **without unmounting**.

```yaml
- name: Etendre lab_lv a 2G (avec resizefs)
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    size: 2G
    resizefs: true   # Also extends the filesystem
    state: present
```

🔍 **Observation**:

- **`lvextend`** extends the LV to 2 GiB (the VG has 5, the space is there).
- **`resizefs: true`** runs `xfs_growfs` (or `resize2fs` for ext4) to extend
  the filesystem **without unmounting**.

**Check**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'df -h /mnt/lvm-data'
# /dev/mapper/lab_vg-lab_lv  2.0G ...
```

**XFS limitation**: `xfs_growfs` can **extend** but not **shrink**. To
shrink, you need `ext4` or unmount + reformat.

## 📚 Exercise 7 — The trap: `vgremove` without cleaning up the LVs

```yaml
# ❌ DANGER: vgremove fails if LVs still exist
- community.general.lvg:
    vg: lab_vg
    state: absent
```

Correct order for the **teardown**:

```yaml
- name: 1. Demonter et retirer fstab
  ansible.posix.mount:
    path: /mnt/lvm-data
    state: absent

- name: 2. Supprimer le LV
  community.general.lvol:
    vg: lab_vg
    lv: lab_lv
    state: absent

- name: 3. Supprimer le VG
  community.general.lvg:
    vg: lab_vg
    state: absent

- name: 4. Liberer le PV
  ansible.builtin.command: pvremove -ff -y /dev/vdb
  changed_when: true

- name: 5. Effacer les signatures LVM du disque
  ansible.builtin.command: wipefs -af /dev/vdb
  changed_when: true
```

🔍 **Observation**: order **exactly the reverse** of the creation. Skipping a
step = failure or LVM orphans. This is exactly what the lab's `cleanup.yaml`
does (`dsoxlab clean modules-rhel-lvm-storage`).

## 🔍 Observations to note

- **LVM pipeline**: PV (`pvcreate`) → VG (`lvg:`) → LV (`lvol:`) → FS
  (`filesystem:`) → mount (`mount:`).
- **`size:` accepts**: absolute values (`100M`), percentages (`50%FREE`),
  relative (`+10G`).
- **`xfs` is the RHEL 7+ default**; `ext4` for `/boot` or when you need to shrink.
- **`resizefs: true`** extends the filesystem live (without unmounting).
- **`UUID=`** in fstab > `/dev/...`, more stable.
- **Teardown order** = reverse of the creation.

## 🤔 Reflection questions

1. You have `lab_vg` with 1 PV of 5 GiB. You want to add 10 GiB via a 2nd
   disk. What is the complete pipeline (modules + order)?

2. Why is LVM preferred over classic partitions for `/var/log/` or
   `/var/lib/postgresql/`? (hint: extensibility, snapshots).

3. `xfs` cannot shrink. You have a 100 GB LV in xfs with 30 GB used.
   How do you go down to 50 GB? (hint: backup, recreate, restore).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **LVM snapshots**: `lvol: snapshot:` to create a point-in-time snapshot.
  Ideal before a risky upgrade (rollback by restoring the snapshot).
- **Stripping**: `lvol: stripes: 2` to spread an LV over several PVs
  (logical RAID 0 performance).
- **Thin provisioning**: `lvol: thinpool:` to over-provision a VG:
  the LVs grow on demand.
- **`community.general.lvol_size:` with `100%VG`**: create an LV that takes
  the whole VG (single-LV-per-VG case).
- **`parted` and `filesystem` labs**: if LVM is overkill for the case, a
  classic partition formatted then mounted is enough. They work on the same
  `/dev/vdb`, and their `setup.yaml` resets the disk.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/modules-rhel/lvm-storage/lab.yml

# Lint your challenge solution
ansible-lint labs/modules-rhel/lvm-storage/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/modules-rhel/lvm-storage/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
