# Nobody can review a wall of ciphertext

## The situation

Encrypting whole files worked, and now the reviews are blind. Your
`host_vars/db1.lab.yml` holds a listening port, a version, a username and exactly
one password, and because of that one password the entire file is ciphertext. A
diff on it says a blob changed. Reviewers approve without knowing whether someone
bumped a port or swapped a credential. Encrypting the file protected the secret
and destroyed the review at the same time.

Your mission, from **control-node.lab**:

1. In `host_vars/db1.lab.yml`, keep the non-sensitive values **readable** and
   encrypt only the password, as a single inline value inside an otherwise plain
   YAML file.
2. Have Ansible pick that value up transparently at run time, with no extra step
   from the caller.
3. Prove on **db1.lab** that both kinds of variable arrive usable side by side:
   the clear username exactly as written, and the decrypted password.
4. Settle the rule for the team: when an inline value is the right call, and when
   the whole file should be encrypted instead.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/chiffrer-fichier-variable/ (in French)

## 🎯 Challenge — Mix encrypted and cleartext variables on `db1.lab`

### ✅ Objective

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

### 🧩 Stuck?

```bash
dsoxlab hint vault-chiffrer-fichier-variable
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/vault/chiffrer-fichier-variable/challenge/solution.yml \
    --vault-password-file=labs/vault/chiffrer-fichier-variable/.vault_password
```

### 🧪 Validation

```bash
pytest -v labs/vault/chiffrer-fichier-variable/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-chiffrer-fichier-variable
```

### 💡 Going further

- `ansible-vault encrypt_string --stdin-name admin_password` to enter
  the value via stdin (not in the shell history).
- Re-encrypt the value without changing the password: edit the YAML and
  regenerate.
