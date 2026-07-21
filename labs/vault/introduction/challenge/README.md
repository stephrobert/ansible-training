# 🎯 Challenge — combining 2 different vault files in a single play

This challenge uses **two encrypted files** (`db_secrets.yml` and
`api_secrets.yml`, already delivered in `challenge/`) in a single playbook.
Both were encrypted with the **same vault password**:
**`lab77-vault-2026`**.

This password is **enforced**, not chosen: the delivered files were
encrypted with it, so it is the only one that opens them.

## ✅ Objective

On **`db1.lab`**, deposit `/tmp/lab77-challenge-result.txt` (mode `0600`)
that proves that **both** encrypted files were decrypted.

| Expected marker in the file | Comes from |
| --- | --- |
| `db_user: app_admin` | `db_secrets.yml` |
| `api_endpoint: https://api.example.com/v1` | `api_secrets.yml` |
| `ChallengeDB2026` (prefix of `db_password`) | `db_secrets.yml` |
| `challenge_api_xyz789` (the `api_key`) | `api_secrets.yml` |

## 🧩 Skeleton to complete

Step 1: check that the lab vault password is in place. The `.vault_password`
file is gitignored (a password is never committed), so it is absent from a
fresh clone. The following command creates it for you:

```bash
scripts/setup-lab-vault-passwords.sh           # creates the lab's .vault_password
cat labs/vault/introduction/.vault_password    # → lab77-vault-2026
```

If you prefer to create it by hand:

```bash
cd labs/vault/introduction/
printf '%s' "lab77-vault-2026" > .vault_password
chmod 0600 .vault_password
```

Step 2: check that you do open the delivered files:

```bash
ansible-vault view \
    --vault-password-file labs/vault/introduction/.vault_password \
    labs/vault/introduction/challenge/db_secrets.yml
```

Step 3: write `challenge/solution.yml`:

```yaml
---
- name: Challenge 77 — combiner 2 fichiers chiffrés sur db1
  hosts: ???
  become: ???
  gather_facts: false
  vars_files:
    - ???                              # db_secrets.yml (chiffré)
    - ???                              # api_secrets.yml (chiffré)

  tasks:
    - name: Déposer le fichier-résultat avec preuve de déchiffrement
      ansible.builtin.copy:
        dest: ???                      # /tmp/lab77-challenge-result.txt
        content: |
          db_user: {{ ??? }}
          db_password: {{ ??? }}
          api_endpoint: {{ ??? }}
          api_key: {{ ??? }}
        mode: ???                      # 0600 (secrets)
      no_log: ???                      # niveau task — pas dans copy:
```

> 💡 **Pitfalls**:
>
> - **`vars_files:`** loads both encrypted AND unencrypted files:
>   Ansible detects the `$ANSIBLE_VAULT` header automatically.
> - **Relative paths**: `vars_files: [db_secrets.yml]` looks from
>   `playbook_dir`. Since your `solution.yml` is in `challenge/`, the
>   path is simply `db_secrets.yml` (the 2 encrypted files are
>   delivered in the same folder).
> - **`no_log: true`** is a **task-level** keyword, not a parameter of the
>   `copy:` module. Placing it at the module level raises an
>   `Unsupported parameters` error.
> - **Mode `0600`** is essential: a file that contains a password
>   must be readable only by root.

## 🚀 Launch

```bash
ansible-playbook \
    --vault-password-file labs/vault/introduction/.vault_password \
    labs/vault/introduction/challenge/solution.yml
```

> The `conftest.py` automatically injects `--vault-password-file` during
> the pytest replay: you do not need to pass it again for the automated
> tests.

## 🧪 Validation

```bash
pytest -v labs/vault/introduction/challenge/tests/
```

6 tests: file exists, `db_user`, `api_endpoint`, prefix of the
`db_password`, `api_key` present, and **idempotence** (a second run of the
playbook must display `changed=0` everywhere in the `PLAY RECAP`, this is the
RHCE criterion).

## 🧹 Reset

```bash
dsoxlab clean vault-introduction
```

## 💡 Going further

- **`ansible-vault rekey`**: change the vault password without touching
  the content (periodic rotation).
- **`--ask-vault-pass`**: interactive input instead of a file.
- **Check that the encrypted files are committable**: `grep
  app_admin db_secrets.yml` must return **no** result.
