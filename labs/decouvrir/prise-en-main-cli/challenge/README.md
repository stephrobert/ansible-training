# 🎯 Challenge — Encrypt a secret with ansible-vault

## ✅ Objective

Write a Bash script `solution.sh` at the root of **this directory** that:

1. Creates a `vault-secret.yml` file containing exactly:

   ```yaml
   api_key: secret-RHCE-2026
   db_password: motdepasse123
   ```

2. Encrypts it with **`ansible-vault encrypt`** using a password provided
   via `--vault-password-file`. The password is written in `.vault-pass`
   (gitignored).

3. **Checks** that the encrypted file starts with `$ANSIBLE_VAULT;1.1;AES256`.

4. **Decrypts** the file (reading via `ansible-vault view --vault-password-file
   .vault-pass`) and checks that the key `api_key: secret-RHCE-2026` is indeed
   present in the output.

5. Exit 0 if everything works, exit 1 otherwise.

Skeleton to complete:

```bash
#!/usr/bin/env bash
set -euo pipefail

VAULT_PASS_FILE="$(dirname "$0")/.vault-pass"
SECRET_FILE="$(dirname "$0")/vault-secret.yml"

# 1. Put the vault password in .vault-pass (any password of your choice)
echo "???" > "$VAULT_PASS_FILE"

# 2. Create the plaintext file (heredoc with api_key + db_password)
cat > "$SECRET_FILE" <<'EOF'
???
EOF

# 3. Encrypt it with ansible-vault (use the appropriate subcommand)
ansible-vault ??? "$SECRET_FILE" --vault-password-file "$VAULT_PASS_FILE"

# 4. Check that the first line is indeed the AES256 header
head -1 "$SECRET_FILE" | grep -q '^\$ANSIBLE_VAULT;1.1;AES256$' \
  || { echo "FAIL : header Vault invalide"; exit 1; }

# 5. Read the decrypted content and check that the api_key key is present
ansible-vault ??? "$SECRET_FILE" --vault-password-file "$VAULT_PASS_FILE" \
  | grep -q '???' \
  || { echo "FAIL : déchiffrement KO"; exit 1; }

echo "Vault OK"
```

> 💡 **Pitfalls**:
>
> - `.vault-pass` must be in mode `0600` (otherwise Ansible warning).
> - The YAML must have the `clé: valeur` structure exactly as requested.
> - `ansible-vault` has 5 main subcommands: `encrypt`, `decrypt`,
>   `view`, `edit`, `rekey`. Choose the one that **reads without modifying the
>   file** for step 5.

## 🧪 Validation

The pytest test runs your `solution.sh` and checks that it returns exit 0
AND that `vault-secret.yml` is indeed encrypted on disk.

```bash
pytest -v labs/decouvrir/prise-en-main-cli/challenge/tests/
```

## 🚀 Going further

- Instead of laying down the password in plaintext in `.vault-pass`, integrate
  it via the **password retrieval client** (a script that reads from a system
  keyring).
- Add **`ansible-vault rekey`** to change the password of a Vault file
  without touching the content.

## 🧹 Reset

To replay the challenge in a clean state:

```bash
dsoxlab clean decouvrir-prise-en-main-cli
```

This target uninstalls/removes what the solution laid down on the managed
nodes (packages, files, services, firewall rules) so that you can replay the
solution from scratch.
