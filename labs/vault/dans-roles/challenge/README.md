# The role ships its own secrets, and nobody can change them

## The situation

The `secured_app` role travels with the credentials it needs, encrypted inside
the role. That solves distribution and creates a new problem: a team that wants
its own database password has to decrypt the role's internals, edit them, and
re-encrypt. So they fork the role. Three forks later, a security fix has to be
applied four times. The role's secrets are its business; the values a caller uses
are not.

Your mission, from **control-node.lab**:

1. Keep the role's secrets **encrypted inside the role**, in the variables file
   the caller is not supposed to touch.
2. Expose them through **public, overridable variables** that point at the
   encrypted ones, so the caller sees a knob and never the ciphertext.
3. Prove the indirection works both ways on **db1.lab**: an untouched default
   resolves to the decrypted secret, and a value overridden from the play wins.
4. Explain the precedence you just relied on, and why the public variable had to
   live where it does for the override to be possible at all.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-dans-roles/ (in French)

## 🎯 Challenge — `vault.yml` pattern in a role

### ✅ Objective

Demonstrate the production pattern: a `secured_app` role with
**`defaults/main.yml`** (non-sensitive, overridable variables) and
**`vars/main.yml`** (vault variables, encrypted). The test validates that an
override by the play works, and that the 2 encrypted secrets are
correctly decrypted at execution.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `db1.lab` | `/tmp/lab81-secured-app.txt` | `user: appuser`, `port: 9999`, `RoleDBPas…` (first 8 chars of the db_password), `role_api_tok_lab81_xyz` |

### 🧩 Stuck?

```bash
dsoxlab hint vault-dans-roles
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/vault/dans-roles/challenge/solution.yml \
    --vault-password-file=labs/vault/dans-roles/.vault_password \
    -e ansible_roles_path=labs/vault/dans-roles/roles
```

### 🧪 Validation

```bash
pytest -v labs/vault/dans-roles/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-dans-roles
```

### 💡 Going further

- **`vault_*` convention + alias**: `secured_app_db_password: "{{ vault_secured_app_db_password }}"` lets you encrypt once and expose a cleartext variable to the rest of the role.
- **`tags:` on the roles** to skip the vault tasks in `--check` mode.
- **Role dependencies**: `meta/main.yml: dependencies` can reference
  another role that loads the vault.
