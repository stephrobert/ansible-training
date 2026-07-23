# Challenge `parted:`

## Statement

On **db1.lab** with a secondary disk **`/dev/vdb`**, write
`solution.yml` that:

1. Creates 3 GPT partitions on `/dev/vdb`:
   - `vdb1`: 500 MiB, flag `[boot, esp]`.
   - `vdb2`: 4 GiB, no particular flag (for ext4).
   - `vdb3`: rest of the disk, flag `[lvm]`.
2. Checks idempotence with a 2nd run.
3. Inspects the final table and displays it via `debug`.

> 🎯 **No skeleton here, on purpose.** By this point you have written enough
> playbooks to start from a blank file, and that is exactly what the EX294
> asks: the exam hands you no canvas. The hints below target the traps of
> this module, not the YAML syntax.

## Success criteria

- `lsblk /dev/vdb` shows 3 partitions with the right sizes.
- 2nd run of the playbook → **`changed: 0`** (idempotent).
- The `debug` displays the 3 partitions with their respective flags.

## 🧩 Stuck?

```bash
dsoxlab hint modules-rhel-parted
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.
