# 🎯 Challenge — Mix encrypted and cleartext variables on `db1.lab`

## ✅ Objective

Reproduce the `encrypt_string` mechanics of the demo lab, but this time
on **`db1.lab`** with a produced file **`/tmp/lab78-challenge.txt`**
containing 3 expected lines.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab78-challenge.txt` |
| Variable `admin_username` | cleartext, exact value `lab78_admin` |
| Variable `admin_password` | encrypted via `encrypt_string`, must start with `Admin…` |
| The file must display | `starts: Admin…`, `length: <N>` |

## 🧩 Stuck?

```bash
dsoxlab hint vault-chiffrer-fichier-variable
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
ansible-playbook labs/vault/chiffrer-fichier-variable/challenge/solution.yml \
    --vault-password-file=labs/vault/chiffrer-fichier-variable/.vault_password
```

## 🧪 Validation

```bash
pytest -v labs/vault/chiffrer-fichier-variable/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean vault-chiffrer-fichier-variable
```

## 💡 Going further

- `ansible-vault encrypt_string --stdin-name admin_password` to enter
  the value via stdin (not in the shell history).
- Re-encrypt the value without changing the password: edit the YAML and
  regenerate.
