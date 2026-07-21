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

## 🧩 Hints

### Expected structure of the role

```text
roles/secured_app/
├── defaults/main.yml      ← secured_app_user, secured_app_port (cleartext, low precedence)
├── vars/main.yml          ← vault_secured_app_db_password, vault_secured_app_api_token (encrypted)
└── tasks/main.yml         ← composes the final marker
```

### Step 1 — Defaults (cleartext)

```yaml
# roles/secured_app/defaults/main.yml
---
secured_app_user: ???       # → "user: appuser"
secured_app_port: ???       # default à 8080, le play l'override à 9999
```

### Step 2 — Vars (encrypted)

```bash
# The lab vault password is generated locally, never committed:
#   ./scripts/setup-lab-vault-passwords.sh
# It creates .vault_password at the lab root, with the right permissions.

cat > roles/secured_app/vars/main.yml <<'YAML'
---
vault_secured_app_db_password: ???       # commence par "RoleDBPas" (9 chars)
vault_secured_app_api_token: ???          # exactement "role_api_tok_lab81_xyz"
secured_app_db_password: "{{ vault_secured_app_db_password }}"
secured_app_api_token: "{{ vault_secured_app_api_token }}"
YAML

ansible-vault encrypt roles/secured_app/vars/main.yml --vault-password-file=.vault_password
```

### Step 3 — Role task

```yaml
# roles/secured_app/tasks/main.yml
---
- name: Déposer le marqueur lab81
  ansible.builtin.copy:
    dest: /tmp/lab81-secured-app.txt
    content: |
      user: {{ secured_app_user }}
      port: {{ secured_app_port }}
      db_starts: {{ secured_app_db_password[:9] }}
      api_token: {{ secured_app_api_token }}
    mode: "0600"
  no_log: ???
```

### Step 4 — `challenge/solution.yml`

```yaml
---
- name: Challenge 81 — invoquer le rôle secured_app sur db1
  hosts: ???
  become: ???
  gather_facts: false
  roles:
    - role: secured_app
      vars:
        secured_app_port: 9999       # override du default
```

> 💡 **Pitfalls**:
>
> - **`defaults/main.yml`** (priority 2) vs **`vars/main.yml`** (priority
>   18): everything in `vars/` **cannot** be overridden by
>   an `--extra-vars` of the play. The users of the role modify the
>   `defaults/`, not the `vars/`.
> - **Indirection pattern**: the encrypted `vars/main.yml` contains
>   `vault_*`, then the cleartext `defaults/main.yml` does
>   `app_var: "{{ vault_app_var }}"`. The role uses `app_var`,
>   the user only sees the `defaults/`.
> - **`ANSIBLE_ROLES_PATH`** must point to the parent folder of the role.
>   Not the role itself.
> - **Distribution of the role**: never include the `.vault_password` in
>   the Galaxy tarball. The user provides their own via
>   `--vault-password-file`.

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
