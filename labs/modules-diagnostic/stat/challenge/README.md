# 🎯 Challenge — `stat:` for system file audit

## ✅ Objective

On **db1.lab**, use `ansible.builtin.stat` to collect **info** on 3 system files,
then write them into a report `/tmp/lab-stat-report.txt`.

| File | Info to collect |
| --- | --- |
| `/etc/passwd` | exists + mode + SHA256 checksum |
| `/etc/shadow` | exists + mode + uid (must be 0 = root) |
| `/etc/sudoers` | exists + mode (must be 0440) |

The report must be a readable `.txt` file with the 3 entries.

## 🧩 Steps

1. **3 parallel `stat:` tasks** (with `get_checksum: true` for the 1st).
2. **`copy: content:`** that assembles a multi-line report via Jinja2.

## 🧩 Skeleton

```yaml
---
- name: Challenge - stat audit
  hosts: db1.lab
  become: true

  tasks:
    - name: Stat /etc/passwd avec checksum SHA256
      ansible.builtin.stat:
        path: ???
        get_checksum: ???
        checksum_algorithm: ???
      register: passwd_stat

    - name: Stat /etc/shadow
      ansible.builtin.stat:
        path: ???
      register: shadow_stat

    - name: Stat /etc/sudoers
      ansible.builtin.stat:
        path: ???
      register: sudoers_stat

    - name: Generer le rapport
      ansible.builtin.copy:
        content: |
          /etc/passwd
            exists: {{ ??? }}
            mode: {{ ??? }}
            sha256: {{ ??? }}

          /etc/shadow
            exists: {{ ??? }}
            mode: {{ ??? }}
            uid: {{ ??? }}

          /etc/sudoers
            exists: {{ ??? }}
            mode: {{ ??? }}
        dest: ???
        mode: "0644"
```

> 💡 **Traps**:
>
> - **`stat:` creates nothing**, it is read-only. A
>   `changed_when: false` is never necessary because the module is
>   natively read-only.
> - **`<var>.stat.exists`**: `true` if the path exists (file OR
>   directory OR link). To distinguish: `<var>.stat.isdir`,
>   `<var>.stat.islnk`.
> - **`<var>.stat.mode`**: string in octal (e.g. `"0644"`). Not an int.
>   Compare with `'0644'` in quotes.
> - **`get_checksum: true`**: adds `<var>.stat.checksum` (sha1 by
>   default). Costly on large files, disabled by default.

## 🚀 Run

```bash
ansible-playbook labs/modules-diagnostic/stat/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/lab-stat-report.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-diagnostic/stat/challenge/tests/
```

## 🧹 Reset

```bash
ansible db1.lab -b -m file -a "path=/tmp/lab-stat-report.txt state=absent"
```

## 💡 Going further

- **`get_attributes: true`**: add the extended attributes (xattrs, SELinux
  contexts) to the report, useful for advanced security audits.
- **`get_mime: true`**: add the MIME type, handy to distinguish a binary from a
  text script.
- **`follow: true`**: follow the symlinks. Disabled by default.
- **Audit pattern**: combine `stat:` × N files + `template:` to generate an
  **HTML report** of the critical permissions.
- **Lint**:

   ```bash
   ansible-lint labs/modules-diagnostic/stat/challenge/solution.yml
   ```
