# You need the vault password just to read a port number

## The situation

Onboarding hit a wall this week. A new colleague wanted to know which port the
web servers listen on. That value is public, uncontroversial, and locked inside
an encrypted `group_vars` file next to an admin token, so answering the question
required handing over the vault password. The team's config and the team's
secrets are living in the same file, and the secret is setting the access rules
for both.

Your mission, from **control-node.lab**:

1. Split each `group_vars/<group>/` in two: the public configuration in clear
   text, the secrets in a **separate encrypted file** loaded from the same place.
2. Adopt a naming convention that makes a sensitive variable recognisable at a
   glance, without opening anything.
3. Confirm Ansible merges both files transparently at run time: prove on
   **web1.lab** that public values and decrypted secrets, coming from the `all`
   group and from the web group, all land in the same play.
4. Check the payoff: `main.yml` is readable, and diffs on it stay reviewable.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/playbooks-mixtes/ (in French)

## 🎯 Challenge — Mix `main.yml` (cleartext) + `vault.yml` (encrypted) per group

### ✅ Objective

Demonstrate the production pattern: a `group_vars/<grp>/main.yml` with
**non-sensitive variables in cleartext**, and a `group_vars/<grp>/vault.yml`
**encrypted** with the passwords / tokens. Both files are
loaded automatically by Ansible at runtime.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `web1.lab` | `/tmp/lab80-challenge.txt` | `Env: lab80`, `Port: 80`, `Admin token starts: lab80_admi`, `Web secret length: 20` |

### 🧩 Stuck?

```bash
dsoxlab hint vault-playbooks-mixtes
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/vault/playbooks-mixtes/challenge/solution.yml \
    --vault-password-file=labs/vault/playbooks-mixtes/.vault_password
```

### 🧪 Validation

```bash
pytest -v labs/vault/playbooks-mixtes/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-playbooks-mixtes
```

### 💡 Going further

- **Convention**: prefix the vault variables with `vault_` to
  document their sensitivity.
- **Two files vs one inline `!vault |` file**: prefer the
  separation on multi-team projects.
- **Precedence**: `group_vars/<grp>/*` > `group_vars/all/*`,
  `webservers` can override a value from `all`.
