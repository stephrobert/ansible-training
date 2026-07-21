# 🎯 Challenge — Mix `main.yml` (cleartext) + `vault.yml` (encrypted) per group

## ✅ Objective

Demonstrate the production pattern: a `group_vars/<grp>/main.yml` with
**non-sensitive variables in cleartext**, and a `group_vars/<grp>/vault.yml`
**encrypted** with the passwords / tokens. Both files are
loaded automatically by Ansible at runtime.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `web1.lab` | `/tmp/lab80-challenge.txt` | `Env: lab80`, `Port: 80`, `Admin token starts: lab80_admi`, `Web secret length: 20` |

## 🧩 Hints

### Expected structure

```text
group_vars/
├── all/
│   ├── main.yml           ← env_name, env_port (cleartext)
│   └── vault.yml          ← vault_admin_token (encrypted)
└── webservers/
    ├── main.yml           ← variables specific to webservers (cleartext)
    └── vault.yml          ← vault_web_secret (encrypted)
```

### Step 1 — Cleartext variables

```yaml
# group_vars/all/main.yml
---
env_name: ???              # doit afficher "Env: lab80"
env_port: ???              # doit afficher "Port: 80"
```

### Step 2 — Sensitive variables (encrypted)

```bash
# The lab vault password is generated locally, never committed:
#   ./scripts/setup-lab-vault-passwords.sh
# It creates .vault_password at the lab root, with the right permissions.

cat > group_vars/all/vault.yml <<'YAML'
---
vault_admin_token: ???     # doit commencer par "lab80_admi" (chars 0-9)
YAML
ansible-vault encrypt group_vars/all/vault.yml --vault-password-file=.vault_password

cat > group_vars/webservers/vault.yml <<'YAML'
---
vault_web_secret: ???      # exactement 20 caractères
YAML
ansible-vault encrypt group_vars/webservers/vault.yml --vault-password-file=.vault_password
```

### Step 3 — Write `challenge/solution.yml`

```yaml
---
- name: Challenge 80 — playbook mixte clair + vault sur webservers
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: Déposer le marqueur lab80
      ansible.builtin.copy:
        dest: ???
        content: |
          Env: {{ env_name }}
          Port: {{ env_port }}
          Admin token starts: {{ vault_admin_token[:10] }}
          Web secret length: {{ vault_web_secret | length }}
        mode: "0600"
      no_log: ???
```

> 💡 **Pitfalls**:
>
> - **`vault_*` convention**: prefix the sensitive variables. Allows
>   **`grep -r vault_ inventory/`** to audit all the secrets.
> - **`group_vars/<grp>/main.yml` + `vault.yml`**: Ansible loads the
>   2 files and merges them. No need for an explicit `vars_files:`.
> - **Precedence**: `group_vars/<grp>/` > `group_vars/all/`. So a
>   variable in `webservers/vault.yml` overrides `all/vault.yml`.
> - **Readable diff**: only `vault.yml` is encrypted. `main.yml` stays
>   in cleartext → readable Git diffs on the non-sensitive vars.

## 🚀 Launch

```bash
ansible-playbook labs/vault/playbooks-mixtes/challenge/solution.yml \
    --vault-password-file=labs/vault/playbooks-mixtes/.vault_password
```

## 🧪 Validation

```bash
pytest -v labs/vault/playbooks-mixtes/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean vault-playbooks-mixtes
```

## 💡 Going further

- **Convention**: prefix the vault variables with `vault_` to
  document their sensitivity.
- **Two files vs one inline `!vault |` file**: prefer the
  separation on multi-team projects.
- **Precedence**: `group_vars/<grp>/*` > `group_vars/all/*`,
  `webservers` can override a value from `all`.
