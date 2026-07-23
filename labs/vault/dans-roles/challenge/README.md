# 🎯 Challenge — `vault.yml` pattern in a role

## ✅ Objective

Demonstrate the production pattern: a `secured_app` role with
**`defaults/main.yml`** (non-sensitive, overridable variables) and
**`vars/main.yml`** (vault variables, encrypted). The test validates that an
override by the play works, and that the 2 encrypted secrets are
correctly decrypted at execution.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `db1.lab` | `/tmp/lab81-secured-app.txt` | `user: appuser`, `port: 9999`, `RoleDBPas…` (first 8 chars of the db_password), `role_api_tok_lab81_xyz` |

## 🧩 Stuck?

```bash
dsoxlab hint vault-dans-roles
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
ansible-playbook labs/vault/dans-roles/challenge/solution.yml \
    --vault-password-file=labs/vault/dans-roles/.vault_password \
    -e ansible_roles_path=labs/vault/dans-roles/roles
```

## 🧪 Validation

```bash
pytest -v labs/vault/dans-roles/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean vault-dans-roles
```

## 💡 Going further

- **`vault_*` convention + alias**: `secured_app_db_password: "{{ vault_secured_app_db_password }}"` lets you encrypt once and expose a cleartext variable to the rest of the role.
- **`tags:` on the roles** to skip the vault tasks in `--check` mode.
- **Role dependencies**: `meta/main.yml: dependencies` can reference
  another role that loads the vault.
