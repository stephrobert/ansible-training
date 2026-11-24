# Three secrets that must never reach a log

## The situation

The application on **db1.lab** needs a config file carrying a database
password, a JWT secret and a Redis token. Last time this was done by hand, the
three values ended up in clear text in the Git history *and* in the CI console
output. The audit left you one rule: secrets live encrypted in the repo, they
are decrypted only at run time, and they appear in **no** Ansible output.

From **control-node.lab**, you build that chain end to end.

Your mission:

1. Keep the vault password in a `0600` file, gitignored, and nowhere else.
2. Encrypt the three secrets in a **Vault YAML file**, then verify on disk that
   it really begins with the `$ANSIBLE_VAULT` header.
3. Consume it through **`vars_files`** to render `/tmp/db1-app.conf` on
   `db1.lab`, owner `root`, mode `0600`.
4. Silence the task that handles them so the values never surface in the
   console — and remember that this keyword belongs to the task, not to the
   module.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premiers-pas-ansible-vault/ (in French)

## 🎯 Challenge — Encrypted application configuration on `db1.lab`

### ✅ Objective

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

### 🧩 Stuck?

```bash
dsoxlab hint premiers-pas-ansible-vault
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Running

From the repo root:

```bash
ansible-playbook labs/premiers-pas/ansible-vault/challenge/solution.yml \
    --vault-password-file=labs/premiers-pas/ansible-vault/challenge/.vault_password
```

### 🧪 Automated validation

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

### 🧹 Reset

```bash
dsoxlab clean premiers-pas-ansible-vault
```

### 💡 Going further

- **`ANSIBLE_VAULT_PASSWORD_FILE=…`** in `.env` or the workstation's
  `~/.bashrc` to stop typing `--vault-password-file`.
- **`ansible-vault rekey`**: change the vault password without
  touching the content (periodic rotation).
- **Secrets precedence**: `vars_files:` > `defaults/main.yml`,
  watch out for collisions.
- **`ansible-lint --profile production`** detects unencrypted secrets
  files and the lack of `no_log:` on sensitive
  tasks.
