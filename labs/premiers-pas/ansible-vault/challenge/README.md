# 🎯 Challenge — Encrypted application configuration on `db1.lab`

## ✅ Objective

Drop an encrypted application configuration on `db1.lab`, containing
**3 different secrets**.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/db1-app.conf` |
| Permissions | `0600`, owner `root` |
| Variable `app_db_password` | must appear in the file |
| Variable `app_jwt_secret` | must appear in the file |
| Variable `app_redis_token` | must appear in the file |
| Secrets source | **encrypted YAML file** (`challenge/files/app_secrets.yml`) |
| Vault password | `challenge/.vault_password` (mode `0600`, gitignored) |

## 🧩 Hints

### Step 1 — Prepare the vault password

```bash
cd labs/premiers-pas/ansible-vault/challenge/

echo "??? choose a strong password ???" > .vault_password
chmod ??? .vault_password
```

### Step 2 — Create the plaintext secrets file

```bash
mkdir -p files
cat > files/app_secrets.yml <<'EOF'
---
app_db_password: ???
app_jwt_secret:  ???
app_redis_token: ???
EOF
```

### Step 3 — Encrypt the file

```bash
ansible-vault ??? files/app_secrets.yml --vault-password-file=.vault_password
```

Check:

```bash
head -3 files/app_secrets.yml      # → must start with $ANSIBLE_VAULT;1.1;AES256
```

### Step 4 — Write `solution.yml`

Skeleton to complete (the `???` are to be guessed):

```yaml
---
- name: Challenge 04b — déposer config applicative chiffrée
  hosts: ???
  become: ???
  gather_facts: false
  vars_files:
    - ???                          # the encrypted file

  tasks:
    - name: Déposer /tmp/db1-app.conf avec les 3 secrets
      ansible.builtin.copy:
        dest: ???
        content: |
          # config app — secrets déchiffrés au runtime
          db_password={{ ??? }}
          jwt_secret={{ ??? }}
          redis_token={{ ??? }}
        owner: ???
        group: ???
        mode: ???
      # Task level, aligned with `ansible.builtin.copy:` and not indented
      # under it: see the trap noted below.
      no_log: ???
```

> 💡 **Traps**:
>
> - **`no_log: true`** is a **task-level** keyword, not a parameter of the
>   `copy:` module. Placing it in the module gives `Unsupported parameters`.
> - **Mode `0600`** essential for `.vault_password` AND for the secrets
>   file dropped. Without it, other system users can steal the
>   content.
> - **`vars_files: [files/app_secrets.yml]`**: path relative to the playbook.
>   With `solution.yml` in `challenge/`, the path is just
>   `files/app_secrets.yml` (not `challenge/files/...`).
> - **The test scans `.vault_password`** to check mode 0600. Mode
>   0644 fails the test, even if decryption works.

## 🚀 Running

From the repo root:

```bash
ansible-playbook labs/premiers-pas/ansible-vault/challenge/solution.yml \
    --vault-password-file=labs/premiers-pas/ansible-vault/challenge/.vault_password
```

## 🧪 Automated validation

```bash
pytest -v labs/premiers-pas/ansible-vault/challenge/tests/
```

The `pytest+testinfra` test validates:

- `/tmp/db1-app.conf` exists on `db1.lab` with mode `0600` and owner `root`.
- The 3 variables (`db_password=`, `jwt_secret=`, `redis_token=`) are
  present in the content.
- The `challenge/files/app_secrets.yml` file is indeed **encrypted**
  (starts with `$ANSIBLE_VAULT`).
- The `challenge/.vault_password` file does have `mode 0600`.
- The solution is **idempotent**: a second run reports no change (RHCE criterion).

## 🧹 Reset

```bash
dsoxlab clean premiers-pas-ansible-vault
```

## 💡 Going further

- **`ANSIBLE_VAULT_PASSWORD_FILE=…`** in `.env` or the workstation's
  `~/.bashrc` to stop typing `--vault-password-file`.
- **`ansible-vault rekey`**: change the vault password without
  touching the content (periodic rotation).
- **Secrets precedence**: `vars_files:` > `defaults/main.yml`,
  watch out for collisions.
- **`ansible-lint --profile production`** detects unencrypted secrets
  files and the lack of `no_log:` on sensitive
  tasks.
