# 🎯 Challenge — `archive` + `unarchive` (back up and restore)

## ✅ Objective

On **db1.lab**, demonstrate the full pipeline:

1. **Prepare**: create `/opt/data-source/` with 3 files
   `file1.txt`, `file2.txt`, `file3.txt` (content `Donnee 1`, `Donnee 2`, `Donnee 3`).
2. **Archive**: produce `/opt/backup/data.tar.gz` (format `gz`) from the source
   directory.
3. **Extract**: restore the archive into `/opt/restored/`. **Idempotent** on the
   2nd run thanks to `creates:`.

## 🧩 Key modules

- `community.general.archive` (FQCN): the **archive** module (create a .tar.gz, .zip, etc.).
- `ansible.builtin.unarchive`: archive extraction (shipped with `ansible-core`).

> ⚠️ The `archive` module lives in **`community.general`**, not in
> `ansible.builtin`. Watch out for the trap: `ansible.builtin.archive` **does
> not raise an error**, the ansible-core routing redirects silently
> (`ansible-doc ansible.builtin.archive` does render the community.general
> page). Your playbook runs, and `ansible-lint --profile production` **rejects**
> it anyway: rule `fqcn[canonical]`. A module that works is not a correctly
> named module.
>
> `unarchive`, on the other hand, is indeed in `ansible.builtin`.

## 🧩 Skeleton

```yaml
---
- name: Challenge - archive + unarchive
  hosts: db1.lab
  become: true

  tasks:
    # Préparation
    - name: Répertoire source
      ansible.builtin.file:
        path: /opt/data-source
        state: directory
        mode: "0755"

    - name: Trois fichiers de données
      ansible.builtin.copy:
        content: "Donnee {{ item }}\n"
        dest: "/opt/data-source/file{{ item }}.txt"
        mode: "0644"
      loop: ???

    # Archivage
    - name: Répertoire de backup
      ansible.builtin.file:
        path: /opt/backup
        state: directory
        mode: "0755"

    - name: Archiver le dossier source
      community.general.archive:
        path: ???
        dest: ???
        format: ???

    # Extraction
    - name: Répertoire pour extraction
      ansible.builtin.file:
        path: /opt/restored
        state: directory
        mode: "0755"

    - name: Extraire l'archive (idempotent via creates)
      ansible.builtin.unarchive:
        src: ???
        dest: ???
        remote_src: ???       # l'archive est sur le managed node, pas sur le control
        creates: ???          # marqueur d'idempotence (le 2e run skippe)
```

> 💡 **`remote_src: true`** is crucial: without it, `unarchive` looks for the
> archive **on the control node side**, not the managed node side, and fails.

**Pitfalls**:

> - **`creates:`** = idempotence marker. Without it, `unarchive` re-extracts
>   on every run → files rewritten, mtimes changed, `changed=1` every time.
> - **`archive`** is in **`community.general`**, not `ansible.builtin`.
>   Correct FQCN: `community.general.archive`.
> - **Archive format**: `unarchive` detects `.tar.gz`, `.zip`, `.tar.bz2`
>   automatically. For exotic formats (`.7z`, `.xz`), go through `command: tar`.
> - **`extra_opts:`**: pass flags to the tar binary. For example
>   `--strip-components=1` to remove the first directory level.

## 🚀 Run

```bash
ansible-playbook labs/modules-fichiers/archive-unarchive/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /opt/data-source /opt/backup /opt/restored"
```

🔍 On the **2nd run**, the `unarchive` task must show `skipped` (proof of the
`creates:`).

## 🧪 Automated validation

```bash
pytest -v labs/modules-fichiers/archive-unarchive/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-fichiers-archive-unarchive
```

## 💡 Going further

- **`format: zip` / `format: bz2` / `format: xz`**: other supported formats.
- **`exclude_path:`** on `archive`: exclude certain files from the archive
  (e.g. `*.log`, `__pycache__/`).
- **Timestamped backup pattern**:

  ```yaml
  dest: "/opt/backup/data-{{ ansible_date_time.iso8601_basic_short }}.tar.gz"
  ```

  Creates a dated archive on every run, non-idempotent by design (but
  useful in cron to keep a history).
- **Lint**:

   ```bash
   ansible-lint labs/modules-fichiers/archive-unarchive/challenge/solution.yml
   ```
