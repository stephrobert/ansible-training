# 🎯 Challenge — Collect `os-release` with `fetch:`

## ✅ Objective

`fetch:` is the **inverse** of `copy:`: it pulls a file back from the **managed
node** to the **control node**. This challenge demonstrates it on **2 hosts**.

## 🧩 Tasks

### Play 1 — Collection on web1 AND db1

Target: `hosts: web1.lab,db1.lab` (2 hosts as an explicit pattern).

For each host, **pull back `/etc/os-release`** into a local file named after
the short hostname (without `.lab`):

| Host | File collected on the control node |
| --- | --- |
| `web1.lab` | `collected/web1-os-release.txt` |
| `db1.lab` | `collected/db1-os-release.txt` |

### Play 2 — web1-specific tag

Target: `hosts: web1.lab` only.

1. Write (`copy: content:`) the file `/etc/lab-tag.txt` on web1 with the
   content `RHCE-LAB-2026`.
2. Pull it back (`fetch:`) to the control node into `collected/web1-tag.txt`.

## 🧩 Stuck?

```bash
dsoxlab hint modules-fichiers-fetch
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🧩 Skeleton

```yaml
---
- name: Play 1 - collecte os-release sur 2 hôtes
  hosts: web1.lab,db1.lab
  become: true

  tasks:
    - name: Rapatrier /etc/os-release vers ./collected/<host>-os-release.txt
      ansible.builtin.fetch:
        src: ???
        dest: ???
        flat: ???

- name: Play 2 - tag spécifique web1
  hosts: web1.lab
  become: true

  tasks:
    - name: Écrire /etc/lab-tag.txt
      ansible.builtin.copy:
        content: ???
        dest: ???
        mode: "0644"

    - name: Rapatrier le tag
      ansible.builtin.fetch:
        src: ???
        dest: ???
        flat: ???
```

> 💡 **Pitfalls**:
>
> - **`fetch:`** copies **from the managed node to the control node** (inverse
>   of `copy:`). For backups, audits, debugging.
> - **`flat: true`**: no subdirectory per host (the file is placed directly
>   in `dest`). Without it, `dest/<hostname>/<src>` is created.
> - **`fail_on_missing: true`**: fails if the source file is absent. By
>   default `false`, the task is marked `skipped`.
> - **`dest/<hostname>/`**: lets you differentiate the fetches of several
>   hosts. Do not combine with `flat: true`.

## 🚀 Run

```bash
ansible-playbook labs/modules-fichiers/fetch/challenge/solution.yml
ls -la collected/
cat collected/web1-tag.txt
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-fichiers/fetch/challenge/tests/
```

The test inspects files **on the control node** (not testinfra/SSH).

## 🧹 Reset

```bash
dsoxlab clean modules-fichiers-fetch
```

## 💡 Going further

- **`fetch: flat: false`** (default): Ansible creates
  `dest/<hostname>/<full_path>`. Useful to preserve the original tree during
  a multi-host audit.
- **Typical use case**: log collection, config dumps, pre-deployment snapshots.
  Combine with `synchronize:` for entire directories.
- **Lint**:

   ```bash
   ansible-lint labs/modules-fichiers/fetch/challenge/solution.yml
   ```
