# 🎯 Challenge — `find:` + automatic cleanup

## ✅ Objective

On **db1.lab**, create 5 `.log` files of various sizes, then use `find:` to
identify those **> 5MB** and delete them in a loop.

## 🧩 Steps

1. Create a folder `/tmp/lab-find-cleanup/` (mode 0755).
2. Create **5 files** `.log` in it:
   - `small1.log` (1MB)
   - `small2.log` (3MB)
   - `big1.log` (10MB)
   - `big2.log` (15MB)
   - `big3.log` (20MB)
3. **`find:`** the `.log` larger than **5MB** in this folder.
4. **`file: state: absent`** in a `loop:` on the result.

At the end, **only** `small1.log` and `small2.log` must remain.

## 🧩 Skeleton

```yaml
---
- name: Challenge - find + cleanup
  hosts: db1.lab
  become: true

  tasks:
    - name: Creer le dossier de test
      ansible.builtin.file:
        path: ???
        state: directory
        mode: "0755"

    - name: Creer 5 fichiers .log
      ansible.builtin.shell: |
        cd /tmp/lab-find-cleanup
        dd if=/dev/zero of=small1.log bs=1M count=1 2>/dev/null
        dd if=/dev/zero of=small2.log bs=1M count=3 2>/dev/null
        dd if=/dev/zero of=big1.log bs=1M count=10 2>/dev/null
        dd if=/dev/zero of=big2.log bs=1M count=15 2>/dev/null
        dd if=/dev/zero of=big3.log bs=1M count=20 2>/dev/null
      args:
        creates: /tmp/lab-find-cleanup/small1.log

    - name: Trouver les .log > 5Mo
      ansible.builtin.find:
        paths: ???
        patterns: ???
        size: ???
      register: big_logs

    - name: Supprimer ces fichiers
      ansible.builtin.file:
        path: ???
        state: ???
      loop: ???
      loop_control:
        label: ???
```

> 💡 **Traps**:
>
> - **`age: -7d`** (negative): files **more recent** than 7 days.
>   `age: 7d` (positive): files **older**. Classic inversion.
> - **`recurse: true`**: descends into the subfolders. Without it, only the
>   direct `paths:` is scanned.
> - **`size:` accepts units**: `1m` (mega), `1g` (giga). Without a unit =
>   bytes.
> - **`<var>.files`** = list of dicts. Iterate with `loop:` + `path:
>   "{{ item.path }}"` to delete them.
> - **`patterns:`**: list of globs (`*.log`, `*.tmp`). For regex:
>   `use_regex: true` + regex patterns.

## 🚀 Run

```bash
ansible-playbook labs/modules-diagnostic/find/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "ls -la /tmp/lab-find-cleanup/"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-diagnostic/find/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-find-cleanup state=absent"
```

## 💡 Going further

- **`age: 7d`**: add a time filter (logs > 5MB **AND** > 7 days).
- **`recurse: true`**: descend into the subfolders.
- **`hidden: true`**: include the `.dotfiles`.
- **Shell pattern**: `find /tmp -name '*.log' -size +5M -delete` is faster than
  `find:` + `loop:` on **tens of thousands** of files, but loses Ansible
  idempotence.
- **Lint**:

   ```bash
   ansible-lint labs/modules-diagnostic/find/challenge/solution.yml
   ```
