# 🎯 Challenge — `copy:` module (deploy an SSH banner)

## ✅ Objective

On **web1.lab**, drop **two files** into `/etc/`:

1. `/etc/ssh/banner-rhce` from a local source file
   (`challenge/files/banner-ssh.txt`). Adding `backup: true` is a
   **production best practice**, recommended but **not verified by the tests**
   (a first run has nothing to back up).
2. `/etc/motd-rhce` from **inline content** (`content:`).

Demonstrates the difference between `src:` (source file) and `content:` (string).

## 🧩 Files to create

### 1) `challenge/files/banner-ssh.txt`

To create on the control node side. Content:

```text
=====================================
   Acces autorise uniquement
   Toute connexion est tracee
=====================================
```

### 2) `challenge/solution.yml`

Skeleton:

```yaml
---
- name: Challenge - module copy (src + content)
  hosts: web1.lab
  become: true

  tasks:
    - name: Déployer le banner SSH (depuis un fichier local)
      ansible.builtin.copy:
        src: ???
        dest: ???
        owner: root
        group: root
        mode: "0644"
        backup: true              # best practice (prod), not verified by the tests

    - name: Marquer le serveur via content inline
      ansible.builtin.copy:
        content: ???
        dest: ???
        owner: root
        group: root
        mode: "0644"
```

## 🧩 Expected output

| File | Source | Content |
| --- | --- | --- |
| `/etc/ssh/banner-rhce` | `files/banner-ssh.txt` | the 4 banner lines |
| `/etc/motd-rhce` | inline | `Serveur RHCE — gere par Ansible` |

> 💡 **Pitfalls**:
>
> - **`src:` vs `content:`**: `src:` pushes a local file from the control
>   node; `content:` writes a string directly. Mutually exclusive.
> - **`src:` path** relative to `<role>/files/` or to the `files/` next to
>   the playbook. No need for the `files/` prefix if the file is in
>   `<role>/files/`.
> - **`backup: true`** creates a timestamped copy before overwriting. A
>   production best practice for shared files (`/etc/ssh/*`), **not verified by
>   the tests** (nothing to back up on a first run).
> - **Mode always quoted**: `"0644"`, not `0644` (octal misinterpreted).
> - **`copy:` is idempotent by checksum**: on an identical 2nd run,
>   `changed=0`.

## 🚀 Run

```bash
ansible-playbook labs/modules-fichiers/copy/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "cat /etc/ssh/banner-rhce"
ansible web1.lab -m ansible.builtin.command -a "cat /etc/motd-rhce"
```

🔍 On the 2nd run after modifying the source file, you will see
`/etc/ssh/banner-rhce.<timestamp>~` appear (proof of `backup: true`).

## 🧪 Automated validation

```bash
pytest -v labs/modules-fichiers/copy/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-fichiers-copy
```

## 💡 Going further

- **`force: false`**: does not overwrite the file if it already exists (useful
  for an initial config you do not want to reset).
- **`remote_src: true`**: the `src:` is on the **managed node** (not on the
  control node). Lets you copy a file from one place to another on the server
  side.
- **`validate:`**: validates the file before overwriting (e.g. `validate: 'sshd
  -t -f %s'` for `sshd_config`). If the validation fails, the original file
  stays intact.
- **Lint**:

   ```bash
   ansible-lint labs/modules-fichiers/copy/challenge/solution.yml
   ```
