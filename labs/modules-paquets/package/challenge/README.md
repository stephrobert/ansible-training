# Standardize the toolbox, and get telnet off the server

## The situation

Two things landed on your desk the same morning. The on-call team is tired of
finding **web1.lab** without an editor worth the name or shell completion, and
the security scan flagged the `telnet` client, whose cleartext protocol has no
business on a server in 2026. Same play, opposite directions: install what is
missing, remove what should not be there. And since the Debian fleet arrives
next quarter, the playbook must not hardcode the RHEL package manager.

Your mission:

1. From **control-node.lab**, bring **web1.lab** up to the standard toolbox
   (editor, shell completion, tree view) in a **single transaction**, not one
   task per package.
2. Remove **`telnet`**, and make sure the removal is proven against the package
   database, not against a command that happens to be missing.
3. Stay **distro-agnostic**: the same playbook must survive the arrival of
   Debian nodes without an `apt` rewrite.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/paquets-services/module-package/ (in French)

## 🎯 Challenge — `package:` module (multi-package, distro-agnostic)

### ✅ Objective

On **web1.lab**, manage 4 packages **with a single module**:

| Package | Desired state |
| --- | --- |
| `vim-enhanced` | `present` |
| `bash-completion` | `present` |
| `tree` | `present` |
| `telnet` | `absent` (cleartext protocol, dangerous) |

Use **`ansible.builtin.package`** rather than `dnf`. This module is
**agnostic**: it chooses `dnf` on RHEL/AlmaLinux, `apt` on
Debian/Ubuntu, etc. Ideal for a single role that must run on several
distributions.

### 🧩 Skeleton

```yaml
---
- name: Challenge - module package
  hosts: ???
  become: ???

  tasks:
    - name: Installer les paquets utiles (3 paquets en une transaction)
      ansible.builtin.package:
        name:
          - ???
          - ???
          - ???
        state: ???

    - name: Supprimer telnet (protocole en clair, sécurité)
      ansible.builtin.package:
        name: ???
        state: ???
```

> 💡 **Traps**:
>
> - **`name:`** accepts a string OR a list. A **list** = a
>   single transaction (faster, more atomic). A `loop:` around
>   a string = N transactions (slow, anti-pattern).
> - **`package` vs `dnf`**: `package` is **agnostic** (RHEL and
>   Debian). If you need specific options (`enablerepo`,
>   `disable_gpg_check`), use `dnf` directly.
> - **`state: absent`** vs **`state: removed`**: both work on
>   `dnf`, but `absent` is universal (RHEL, Debian, …). Prefer
>   `absent`.
> - **pytest test**: uses `host.package("...")` which queries the
>   RPM/dpkg database. No need to replay the playbook if you clean up
>   manually with `dnf`.

### 🚀 Launch

```bash
ansible-playbook labs/modules-paquets/package/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "rpm -q vim-enhanced bash-completion tree"
ansible web1.lab -m ansible.builtin.command -a "rpm -q telnet" || echo "telnet absent (OK)"
```

### 🧪 Automated validation

```bash
pytest -v labs/modules-paquets/package/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-paquets-package
```

### 💡 Going further

- **`package` vs `dnf`**: prefer `package` when the code can run on
  several distros. Prefer `dnf` (or `apt`) when you need
  **specific options** (`enablerepo`, `disable_gpg_check`, etc.): see
  lab 37.
- **`package` + list**: `package` accepts a list of packages in `name:`:
  a single transaction instead of N. Faster and more atomic than a
  `loop:`.
- **Lint**:

   ```bash
   ansible-lint labs/modules-paquets/package/challenge/solution.yml
   ```
