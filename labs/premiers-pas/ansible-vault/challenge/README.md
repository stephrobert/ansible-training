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

## 🧩 Stuck?

```bash
dsoxlab hint premiers-pas-ansible-vault
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

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
