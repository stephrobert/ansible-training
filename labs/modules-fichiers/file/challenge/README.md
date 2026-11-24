# Prepare the release tree before the first deploy

## The situation

The dev team ships **myapp** to **web1.lab** on Thursday and expects the
filesystem to be ready: a versioned release directory, a `current` symlink the
service reads, and a log directory the application can write to without running
as root. The previous hand-made attempt left a stale `/etc/myapp-old.conf`
behind that the app still picks up. You prepare the ground from
**control-node.lab**, in a playbook that will be replayed on every release.

Your mission:

1. Build the release tree on **web1.lab**: **`/opt/myapp/releases/v1.0.0`**
   (mode `0755`, root) and **`/opt/myapp/shared/logs`** (mode `0750`, owned by
   `nobody`) so the app writes its logs without privileges.
2. Point **`/opt/myapp/current`** at the `v1.0.0` release, **overwriting** any
   symlink already aiming elsewhere.
3. Remove the leftover **`/etc/myapp-old.conf`** and drop the init marker
   **`/var/log/myapp-init.timestamp`** (mode `0644`).

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/modules/fichiers/module-file/ (in French)

## 🎯 Challenge — `file:` module (release tree)

### ✅ Objective

On **web1.lab**, build a typical **"release" tree** for application deployment,
exercising the **5 states** of the `ansible.builtin.file` module.

| Task | `state:` | Target |
| --- | --- | --- |
| Release directory | `directory` | `/opt/myapp/releases/v1.0.0` (mode 0755, owner root) |
| Logs directory | `directory` | `/opt/myapp/shared/logs` (mode 0750, owner+group nobody) |
| Current symbolic link | `link` | `/opt/myapp/current` → `/opt/myapp/releases/v1.0.0` |
| Removal of an old config | `absent` | `/etc/myapp-old.conf` (if it exists) |
| Init marker | `touch` | `/var/log/myapp-init.timestamp` (mode 0644) |

### 🧩 Stuck?

```bash
dsoxlab hint modules-fichiers-file
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🧩 Skeleton

```yaml
---
- name: Challenge - module file
  hosts: web1.lab
  become: true

  tasks:
    - name: Répertoire de release
      ansible.builtin.file:
        path: ???
        state: ???
        owner: root
        mode: "0755"

    - name: Répertoire de logs (owner nobody)
      ansible.builtin.file:
        path: ???
        state: ???
        owner: ???
        group: ???
        mode: "0750"

    - name: Symlink current → release
      ansible.builtin.file:
        src: ???
        dest: ???
        state: ???
        force: ???

    - name: Supprimer ancienne config
      ansible.builtin.file:
        path: ???
        state: ???

    - name: Marqueur d'init (touch)
      ansible.builtin.file:
        path: ???
        state: ???
        mode: "0644"
```

> 💡 **Pitfalls**:
>
> - **`state:`** = `directory`, `file`, `link`, `hard`, `touch`,
>   `absent`. Classic confusion: `file` does not create the file
>   (use `touch` to create, or `copy:` to place content).
> - **`recurse: true`** on a directory applies mode/owner/group to
>   the whole tree. Watch out for performance on large volumes.
> - **`state: link`** + `src:` + `force: true`**: replaces an existing
>   link. Without `force`, modification refused if the link already exists.
> - **`mode: u+x`** (symbolic) accepted in addition to `"0755"`. Useful to
>   add a bit without overwriting the others.

### 🚀 Run

```bash
ansible-playbook labs/modules-fichiers/file/challenge/solution.yml
ansible web1.lab -m ansible.builtin.command -a "ls -la /opt/myapp/"
```

### 🧪 Automated validation

```bash
pytest -v labs/modules-fichiers/file/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean modules-fichiers-file
```

### 💡 Going further

- **`recurse: true`**: on `state: directory`, applies `mode/owner/group` to
  the whole tree (recursively).
- **`hard:`**: creates a hard link (instead of a symlink).
- **Blue/green release pattern**: place **two** symlinks (`current`, `next`)
  that point to two different releases, and swap them
  atomically via `state: link, force: true`.
- **Lint**:

   ```bash
   ansible-lint labs/modules-fichiers/file/challenge/solution.yml
   ```
