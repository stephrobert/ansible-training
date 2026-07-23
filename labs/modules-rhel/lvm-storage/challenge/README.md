# 🎯 Challenge — Complete LVM pipeline (PV → VG → LV → FS → mount)

## ✅ Objective

On **db1.lab**, the secondary disk **`/dev/vdb`** (5 GiB) is blank: the
lab setup made it so, with no label or partition. Write `solution.yml`
that brings the machine into this state:

1. `/dev/vdb` is initialized as a **Physical Volume** and attached to the **Volume
   Group `lab_vg`**.
2. A **Logical Volume `lab_lv`** of **1 GiB** is carved out of `lab_vg`.
3. `lab_lv` carries an **xfs** filesystem.
4. The volume is **mounted on `/mnt/lvm-data`** with the options
   `defaults,noatime`, and the corresponding entry is in `/etc/fstab`:
   the mount must come back on its own after a reboot.
5. A 2nd run of the playbook changes nothing (idempotent).

> The PV is placed **directly on the whole disk**, with no prior partition:
> LVM does not need one, and it is the most common pipeline
> for a dedicated disk.

## 🧩 Skeleton to complete

```yaml
---
- name: Challenge — pipeline LVM complet sur db1
  hosts: ???
  become: ???
  tasks:
    - name: Créer le VG sur le disque secondaire
      community.general.lvg:
        vg: ???                              # see the objective
        pvs: ???                             # the whole disk
        state: present

    - name: Créer le LV (cf. objectif pour la taille)
      community.general.lvol:
        vg: ???
        lv: ???
        size: ???

    - name: Formater le LV
      community.general.filesystem:
        fstype: ???
        dev: ???                             # /dev/<vg>/<lv>

    - name: Monter le LV (entrée fstab + actif maintenant)
      ansible.posix.mount:
        path: ???
        src: ???
        fstype: ???
        opts: ???                            # 2 options separated by comma
        state: ???                           # mounts AND writes into fstab
```

> 💡 **Traps**:
>
> - **The module that manages the VG also initializes the PV**: `pvcreate` then
>   `vgcreate` in one task. No need for a separate `command:`.
> - **`state: mounted`** vs `state: present`: only `mounted` modifies
>   `/etc/fstab` **and** mounts right away. `present` only writes the fstab
>   line (nothing mounted before the next reboot).
> - **`noatime`**: fstab option that removes writing the access time.
>   The tests look for it in `findmnt -no OPTIONS` **and** in
>   `/etc/fstab`: an option passed only by hand at mount time would not
>   survive the reboot.
> - **The mount point**: `state: mounted` creates the directory if it is
>   missing, a dedicated `file:` task is superfluous.

## 🚀 Run

Once `solution.yml` is complete, run it against `db1.lab`:

```bash
ansible-playbook labs/modules-rhel/lvm-storage/challenge/solution.yml
```

The `PLAY RECAP` must show `failed=0`. Run it a second time: a
`changed=0` confirms idempotence.

## 🧪 Validation

> ⏱️ **One test reboots db1** (about 90 s). It is marked `slow`, and it is
> there on purpose: persistence after a restart is the trap that fails RHCSA
> and RHCE candidates, and reading the config file proves nothing about it.
> While you iterate, you can leave it out:
>
> ```bash
> pytest -m 'not slow' labs/modules-rhel/lvm-storage/challenge/tests/
> ```
>
> Run the full suite at least once before considering the challenge done.

```bash
pytest -v labs/modules-rhel/lvm-storage/challenge/tests/
```

The tests check on db1:

- `/dev/vdb` is a PV, member of the VG `lab_vg`.
- `lab_lv` exists in `lab_vg` and is about 1 GiB.
- `/dev/lab_vg/lab_lv` is formatted as xfs.
- `/mnt/lvm-data` is mounted on the LV, as xfs, with `noatime`.
- `/etc/fstab` carries the mount entry (type, device and `noatime`).
- The 2nd run of the playbook reports no more `changed`.

## 🧹 Reset

To replay the challenge from a neutral state:

```bash
dsoxlab clean modules-rhel-lvm-storage
```

The cleanup unmounts, removes the fstab entry, deletes LV, VG and PV, then makes
`/dev/vdb` blank: you can rerun the solution from scratch.

## 💡 Going further

- **`ansible-lint --profile production`**: validate the quality of your solution.

  ```bash
  ansible-lint --profile production labs/modules-rhel/lvm-storage/challenge/solution.yml
  ```

  Expected output: `Passed: 0 failure(s), 0 warning(s)`.

- **Extend the volume**: the VG keeps 4 GiB free. Bump `lab_lv` to 2 GiB
  with `resizefs: true` and watch `df -h /mnt/lvm-data` without unmounting.

- **Edge cases**: think about the error scenarios (host unavailable,
  missing dependency, invalid value) that your solution could
  hit in production. How do you handle them (`block/rescue`,
  `failed_when`, `assert`)?
