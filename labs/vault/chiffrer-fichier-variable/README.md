# Lab 78 — Encrypt a file OR an inline variable

> 💡 **Prerequisite**: `ansible all -m ansible.builtin.ping` replies `pong` on the 4 VMs.

## 🧠 Recap

🔗 [**Encrypt a file or a variable**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/chiffrer-fichier-variable/)

Ansible Vault offers **two complementary approaches** to encryption:

| Approach | Command | Use case |
|---|---|---|
| **Complete file** | `ansible-vault encrypt fichier.yml` | Several related secrets (lab 77) |
| **Inline variable** | `ansible-vault encrypt_string 'valeur'` | Mix cleartext + encrypted values in the same YAML |

The **inline mode (encrypt_string)** is **more readable** in Git diffs: you see that the variable changes (and the surrounding context stays readable), without exposing the value. Ideal for `group_vars/all.yml` which mostly contains public values (ports, versions) and **a few** secrets.

**Format** of an encrypted inline variable in a YAML:

```yaml
admin_username: lab78_admin                  # ← clair (lisible dans le diff)
admin_password: !vault |                     # ← VALEUR seulement chiffrée
          $ANSIBLE_VAULT;1.1;AES256
          30613465643765383...
          6265336366626535...
```

The **YAML tag `!vault |`** signals to Ansible that the multi-line value that follows must be decrypted at runtime.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Encrypt **a single value** with `ansible-vault encrypt_string`.
2. **Mix** cleartext values and encrypted values in the same YAML file.
3. Understand **when to prefer** `encrypt_string` over a full `encrypt`.
4. **Re-encrypt** an existing variable.
5. Use the YAML tag **`!vault |`** in `group_vars/`/`host_vars/`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/vault/chiffrer-fichier-variable/
ls -la inventory/group_vars/
cat .vault_password
```

## ⚙️ Target tree

```text
labs/vault/chiffrer-fichier-variable/
├── README.md
├── .vault_password               ← vault password (mode 0600)
├── inventory/
│   ├── hosts.yml                 ← the lab's local inventory
│   └── group_vars/
│       └── all.yml               ← MIXED: cleartext + encrypt_string
├── playbook.yml                  ← consumes admin_username + admin_password
└── challenge/
    ├── README.md
    ├── solution.yml              ← challenge on db1.lab
    └── tests/
        └── test_encrypt_string.py
```

## 📚 Exercise 1 — Read the mixed cleartext/encrypted file

```bash
cat inventory/group_vars/all.yml
```

Output:

```yaml
---
admin_username: lab78_admin                  # ← clair
admin_password: !vault |                     # ← inline encrypt_string
          $ANSIBLE_VAULT;1.1;AES256
          30613465643765383...
```

🔍 **Observation**: only the **value** of `admin_password` is encrypted. The **name of the variable** stays readable in Git, which makes code reviews easier ("Ah, we are adding admin_password") without exposing the secret.

## 📚 Exercise 2 — View an inline variable

```bash
ansible-vault view inventory/group_vars/all.yml --vault-password-file=.vault_password
```

🔍 **Observation**: `view` also works on files with **mixed encryption**: it decrypts only the `!vault |` values and leaves the rest as is.

## 📚 Exercise 3 — Create a new encrypted variable

```bash
ansible-vault encrypt_string \
  --vault-password-file=.vault_password \
  --name 'db_password' \
  'MonNouveauSecretDB2026'
```

Output: a YAML block ready to paste into `inventory/group_vars/all.yml`:

```yaml
db_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
```

🔍 **Observation**: no interactive input of the secret, it is passed as a CLI argument. **Warning**: this secret appears in `bash_history`. Better: use `--encrypt-vault-id default` + input via stdin.

## 📚 Exercise 4 — Input via stdin (more secure)

```bash
echo -n 'MonSecretViaStdin' | ansible-vault encrypt_string \
  --vault-password-file=.vault_password \
  --name 'api_key' \
  --stdin-name api_key
```

🔍 **Observation**: the value does **not** appear in `bash_history`. For automation (CI/CD), this is the recommended pattern.

## 📚 Exercise 5 — Run the playbook

```bash
ansible-playbook -i inventory/hosts.yml \
  --vault-password-file=.vault_password \
  playbook.yml
```

Expected output: `changed=1`. The playbook uses `admin_password` as a normal variable, transparent decryption.

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab "sudo cat /tmp/lab78-encryptstring.txt"
```

Output:

```text
username: lab78_admin
password length: 17
password starts: Admin
```

## 📚 Exercise 6 — Difference inline vs complete file

| Criterion | Complete file (`encrypt`) | Inline (`encrypt_string`) |
|---|---|---|
| Git diff readability | ❌ The whole file changes | ✅ Only the concerned block changes |
| Granularity | All the secrets of a file | A single value at a time |
| Mix cleartext + encrypted | ❌ Everything encrypted | ✅ Cleartext + encrypted together |
| Interactive editing | `ansible-vault edit` | Manual (re-generate encrypt_string) |
| Performance | A single decryption pass | N passes (one per variable) |

**Recommendation**: `encrypt_string` for `group_vars/all.yml` (mixed), `encrypt` for a `vars/secrets.yml` dedicated to pure secrets.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must display `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) rather than the short name (`ansible-lint --profile
  production` checks this).
- **Targeting convention**: this lab targets db1.lab; to adapt it to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then run it again.
- **Isolated reset**: `dsoxlab clean <id-du-lab>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why is `encrypt_string` preferable for `group_vars/all.yml` which mostly contains public values?

2. What happens if you **edit manually** a `!vault |` block (e.g. change one hex character)?

3. How do you **rotate** a single inline variable without touching the others?

4. Why is `--stdin-name` preferable to passing the value as a CLI argument?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) targets `db1.lab` and demonstrates that the variables `admin_username` (cleartext) + `admin_password` (inline encrypted) are decrypted correctly. Automated tests via `pytest+testinfra` (4 tests).

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Multi vault-id** (lab 79): encrypt_string with different vault-ids for dev/prod.
- **`!vault |` in roles**: usable in `defaults/main.yml` or `vars/main.yml` (lab 81).
- **Re-encrypt all the variables**: `ansible-vault rekey inventory/group_vars/all.yml`.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile=production .
```

The linter does not touch the `!vault |` blocks: it only checks the quality of the classic Ansible code around them.
