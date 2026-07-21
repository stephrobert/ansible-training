# 🎯 Challenge — `authorized_key` multi-user with restrictions

## ✅ Objective

On **db1.lab**, provision **3 different SSH keys**:

1. **alice's personal key**: free (no restrictions).
2. **bob's personal key**: restricted (`from="10.10.20.0/24"` + `no-pty`).
3. **Service key** in alice's account: forced command
   (`command="/usr/local/bin/backup.sh"`) + session restrictions.

## 🧩 The key material is already there

`dsoxlab run` generates alice's and bob's keypairs for you, on the control node,
under the lab's `files/` directory:

```text
labs/modules-utilisateurs/authorized-key/files/
├── alice.pub.key       # PRIVATE key (misleading name, kept for compatibility)
├── alice.pub.key.pub   # PUBLIC key  <- this is the one you deploy
├── bob.pub.key
└── bob.pub.key.pub
```

Read the **`.pub.key.pub`** files: `.pub.key` is the private key, despite its
name. The keys are gitignored, so they do not exist in a fresh clone: that is
precisely why the setup creates them.

> ⚠️ Do not regenerate or delete them. The comment carried by each key
> (`alice@laptop`, `bob@laptop`) is checked by the pytest tests, and the setup
> only regenerates a pair when its private key is missing: deleting it would
> hand you a different public key from the one already deployed.

## 🧩 Module to use: `ansible.posix.authorized_key`

| Option | Effect |
| --- | --- |
| `user:` | Target account (`alice`, `bob`). |
| `key:` | The public key (full string). |
| `state: present` | Adds if absent (idempotent). |
| `key_options:` | Prefixes the key with OpenSSH options (`from=`, `command=`, `no-pty`, etc.). |

## 🧩 Skeleton

```yaml
---
- name: Challenge - authorized_key multi-users
  hosts: db1.lab
  become: true

  vars:
    backup_service_key: "ssh-ed25519 AAAA<contenu_pubkey> backup@service"

  tasks:
    - name: Créer alice et bob
      ansible.builtin.user:
        name: ???
        state: present
        shell: /bin/bash
      loop: ???

    - name: Clé personnelle d'alice (libre)
      ansible.posix.authorized_key:
        user: ???
        key: "{{ lookup('file', ???) }}"
        state: present

    - name: Clé personnelle de bob (restreinte)
      ansible.posix.authorized_key:
        user: ???
        key: "{{ lookup('file', ???) }}"
        key_options: ???
        state: present

    - name: Clé de service backup pour alice (commande forcée)
      ansible.posix.authorized_key:
        user: ???
        key: ???
        key_options: ???
        state: present
```

> 💡 **`key_options:`** is a comma-separated **string** of options:
>
> ```text
> 'command="/usr/local/bin/backup.sh",no-pty,no-X11-forwarding,no-port-forwarding'
> ```
>
> For the service key, you must generate **your own static ed25519 public
> key** (e.g. with `ssh-keygen -t ed25519 -N "" -C "backup@service"` to get
> the string) and paste it into `vars:`.

**Traps**:

> - **`exclusive: true`**: replaces **all** existing keys with the one
>   provided. Anti-pattern if you just want to **add**,
>   risk of blocking access by removing the instructor's key.
> - **`key:`** = the **full** public key (`ssh-ed25519 AAA…
>   user@host`). Not only the base64 part.
> - **`state: present`** + key already present = idempotent, no
>   modification. But the order of the keys can change in
>   `authorized_keys`, not a bug.
> - **`manage_dir: true`** (default): creates `~/.ssh/` with the right
>   permissions (0700). Without it, the key can be ignored by sshd
>   (permissions too open).

## 🚀 Run

```bash
ansible-playbook labs/modules-utilisateurs/authorized-key/challenge/solution.yml
ansible db1.lab -b -m ansible.builtin.command -a "cat /home/alice/.ssh/authorized_keys"
ansible db1.lab -b -m ansible.builtin.command -a "cat /home/bob/.ssh/authorized_keys"
```

## 🧪 Automated validation

```bash
pytest -v labs/modules-utilisateurs/authorized-key/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean modules-utilisateurs-authorized-key
```

## 💡 Going further

- **`exclusive: true`**: replaces **all** the user's keys with the one(s)
  provided. Handy to purge orphan keys in a single run.
- **`validate_certs:`**: on `manage_dir: false`, does not touch
  `~/.ssh/` (useful if managed by another tool).
- **Audit the active keys**: `ansible all -b -m ansible.builtin.shell -a
  "for u in $(getent passwd | cut -d: -f1); do echo == $u ==; cat
  /home/$u/.ssh/authorized_keys 2>/dev/null; done"`.
- **Lint**:

   ```bash
   ansible-lint labs/modules-utilisateurs/authorized-key/challenge/solution.yml
   ```
