# 🎯 Challenge — Shell aliases block with `blockinfile`

## ✅ Objective

On **db1.lab**, create the file **`/etc/profile.d/aliases-rhce.sh`** and add to
it a **block of aliases delimited by markers**, idempotent.

## 🧩 Expected output

The file should look like:

```bash
# BEGIN ALIASES RHCE
alias ll='ls -lah'
alias gs='git status'
alias ports='ss -tulpn'
# END ALIASES RHCE
```

If you re-run the playbook, **the block stays unique** (no duplication).
This is the great advantage of `blockinfile` over `lineinfile`: it manages a
**complete block** instead of a single line.

## 🧩 Module to use: `ansible.builtin.blockinfile`

Key options:

| Option | Effect |
| --- | --- |
| `path:` | File to modify. |
| `create: true` | Creates the file if it does not exist (default: false). |
| `block:` | The content of the block (multi-line via `\|`). |
| `marker:` | Marker format. **Must contain `{mark}`** which will be replaced by `BEGIN` or `END`. |
| `mode:` | File permissions. |

## 🧩 Skeleton

```yaml
---
- name: Challenge - blockinfile (aliases shell)
  hosts: db1.lab
  become: true

  tasks:
    - name: Bloc d'aliases dans /etc/profile.d/aliases-rhce.sh
      ansible.builtin.blockinfile:
        path: ???
        create: ???
        mode: "0644"
        marker: "# {mark} ALIASES RHCE"
        block: |
          ???
          ???
          ???
```

> 💡 **Pitfalls**:
>
> - **`marker:`** defines the begin/end tags of the block. Default
>   `# {mark} ANSIBLE MANAGED BLOCK` where `{mark}` = `BEGIN`/`END`. If
>   you call `blockinfile` twice on the same file without changing
>   `marker:`, the 2nd one replaces the 1st.
> - **Custom `marker:`**: `marker: "# {mark} aliases-rhce"` to manage
>   several distinct blocks in the same file.
> - **`create: true`**: creates the file if it does not exist. Without it,
>   failure if the file is absent.
> - **`block:`** accepts a multi-line string (`|`) or a list of strings.
>   The content is inserted as-is between the markers.

## 🚀 Run

```bash
ansible-playbook labs/modules-fichiers/blockinfile/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/profile.d/aliases-rhce.sh"
```

🔍 **Idempotence test**:

```bash
ansible-playbook labs/modules-fichiers/blockinfile/challenge/solution.yml
# On the 2nd run: changed=0 (the block is already compliant)
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-fichiers/blockinfile/challenge/tests/
```

The test checks in particular that the marker `# BEGIN ALIASES RHCE` appears
**exactly once** in the file (proof of idempotence).

## 🧹 Reset

```bash
dsoxlab clean modules-fichiers-blockinfile
```

## 💡 Going further

- **Several blocks in one file**: use **different markers** so they do not
  overwrite each other (`# {mark} BLOC_A`, `# {mark} BLOC_B`).
- **`insertafter:` / `insertbefore:`**: place the block relative to an existing
  pattern. For example `insertafter: '^# Custom config'`.
- **Removing the block**: `state: absent` cleanly removes the block
  (markers included).
- **Lint**:

   ```bash
   ansible-lint labs/modules-fichiers/blockinfile/challenge/solution.yml
   ```
