# 🎯 Challenge — Mix `main.yml` (cleartext) + `vault.yml` (encrypted) per group

## ✅ Objective

Demonstrate the production pattern: a `group_vars/<grp>/main.yml` with
**non-sensitive variables in cleartext**, and a `group_vars/<grp>/vault.yml`
**encrypted** with the passwords / tokens. Both files are
loaded automatically by Ansible at runtime.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `web1.lab` | `/tmp/lab80-challenge.txt` | `Env: lab80`, `Port: 80`, `Admin token starts: lab80_admi`, `Web secret length: 20` |

## 🧩 Stuck?

```bash
dsoxlab hint vault-playbooks-mixtes
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

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
