# One vault password means the interns can read production

## The situation

Every secret in the repository is encrypted with the same vault password, and
that password is handed to anyone who needs to deploy to dev. Which means the
intern who deployed to dev this morning can decrypt the production database
credentials, and nothing in the tooling would stop them or even record it. The
secrets are encrypted. They are not compartmented, and that is a different thing.

Your mission, from **control-node.lab**:

1. Give each environment its **own labelled vault identity** and its own password,
   so holding the dev key decrypts dev and nothing else.
2. Lay the secrets out per environment under `group_vars/`, dev on **web1.lab**
   and prod on **db1.lab**, each group carrying only what belongs to it.
3. Run a single play across **both** environments and have Ansible decrypt each
   file with the right identity, proving the two are never confused.
4. Read the encrypted header and say which identity a file belongs to without
   decrypting it, then state who on the team gets which password.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-id-multiples/ (in French)

## 🎯 Challenge — Separate `dev` and `prod` vault-ids

### ✅ Objective

Demonstrate that **2 different vault-ids** (`dev` and `prod`) decrypt
correctly their **own files** on their **own hosts**.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `web1.lab` (group `dev`) | `/tmp/lab79-challenge-web1.lab.txt` | `dev-db.example.com`, `Environnement: dev`, `length: 12` |
| `db1.lab` (group `prod`) | `/tmp/lab79-challenge-db1.lab.txt` | `prod-db.example.com`, `Environnement: prod`, `length: 26` |

### 🧩 Stuck?

```bash
dsoxlab hint vault-id-multiples
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/vault/id-multiples/challenge/solution.yml \
    --vault-id dev@labs/vault/id-multiples/.vault_password_dev \
    --vault-id prod@labs/vault/id-multiples/.vault_password_prod \
    -i labs/vault/id-multiples/inventory/hosts.yml
```

### 🧪 Validation

```bash
pytest -v labs/vault/id-multiples/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-id-multiples
```

### 💡 Going further

- **3+ vault-ids** (dev/staging/prod/secret): Ansible tries each
  vault-id in cascade until it finds the right one.
- **`@prompt`** instead of a file: `--vault-id prod@prompt` to
  enter it interactively.
- **`server_list:`** in `ansible.cfg` for multi-Galaxy + multi-vault.
