# Lab 77 — Introduction to Ansible Vault (encrypting a complete file)

> 💡 **Prerequisite**: `ansible all -m ansible.builtin.ping` replies `pong` on the 4 VMs.

## 🧠 Recap

🔗 [**Introduction to Ansible Vault**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/ansible-vault-introduction/)

**Ansible Vault** encrypts files containing secrets (passwords, API tokens, private keys) with **AES256**. These files can be committed to Git **safely**: the encryption protects their content. At runtime, Ansible **decrypts them on the fly** with a vault password provided via `--vault-password-file` or `--ask-vault-pass`.

It is Ansible's **native mechanism** for managing secrets, without any external dependency (HashiCorp Vault, AWS Secrets Manager). Essential for the RHCE EX294.

**Encrypted file format**:

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961...   ← encrypted payload (hex)
6136353338613232633836333261396531376630...
```

The **header** (`$ANSIBLE_VAULT;1.1;AES256`) lets Ansible recognize the format automatically.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Encrypt** a complete YAML file with `ansible-vault encrypt`.
2. **View** an encrypted file without decrypting it (`ansible-vault view`).
3. **Edit** an encrypted file (`ansible-vault edit`), transparent editing.
4. **Run a playbook** that consumes an encrypted file.
5. **Re-encrypt** a file with a new password (`ansible-vault rekey`).
6. **Decrypt** a file to cleartext (`ansible-vault decrypt`), for exceptional debugging.

## 🔧 Preparation

The vault password of this lab is **`lab77-vault-2026`**. It lives in
`.vault_password`, which is **gitignored**: a password is never committed,
even a pedagogical one. It is therefore absent from a fresh clone, and it is
the following command that creates it:

```bash
scripts/setup-lab-vault-passwords.sh    # creates the .vault_password files of the vault labs
```

```bash
cd $ANSIBLE_TRAINING/labs/vault/introduction/
ls -la                         # see the structure
cat .vault_password            # → lab77-vault-2026 (mode 0600 enforced)
```

This same password opens the two encrypted files delivered with the challenge
(`challenge/db_secrets.yml` and `challenge/api_secrets.yml`): it is **enforced**
by them, it is not a free choice.

## ⚙️ Target tree

```text
labs/vault/introduction/
├── README.md                  ← this file
├── .vault_password            ← vault password (mode 0600, gitignored)
├── secret.yml                 ← YOU create it in exercise 1 (encrypted, commitable!)
├── playbook.yml               ← YOU create it in exercise 4 (consumes secret.yml)
└── challenge/
    ├── README.md
    ├── db_secrets.yml         ← delivered encrypted
    ├── api_secrets.yml        ← delivered encrypted
    ├── solution.yml           ← YOU write it (challenge on db1.lab)
    └── tests/
        └── test_functional.py
```

## 📚 Exercise 1: Create and encrypt a secrets file

The tutorial works on **your own** `secret.yml` file: creating it is already
the essential gesture to learn.

```bash
cd $ANSIBLE_TRAINING/labs/vault/introduction/

cat > secret.yml <<'EOF'
---
db_password: "MotDePasseDemo2026"
api_token: "tok_demo_abc123xyz789"
EOF

ansible-vault encrypt secret.yml --vault-password-file=.vault_password
cat secret.yml | head -3
```

Expected output:

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961333337353636643636393265...
6136353338613232633836333261396531376630623766330a663566666463...
```

🔍 **Observation**: without the password, it is **impossible** to recover the original content. The file can be committed to public GitHub: confidentiality is guaranteed by AES256.

## 📚 Exercise 2 — View the encrypted content

```bash
ansible-vault view secret.yml --vault-password-file=.vault_password
```

Output:

```yaml
---
db_password: "MotDePasseDemo2026"
api_token: "tok_demo_abc123xyz789"
```

🔍 **Observation**: `view` decrypts **temporarily in memory** for display, **without modifying** the file on disk. The file stays encrypted.

## 📚 Exercise 3 — Edit an encrypted file

```bash
ansible-vault edit secret.yml --vault-password-file=.vault_password
```

Opens in `$EDITOR` (vim/nano), decrypts **in memory**, you edit, save, and it **re-encrypts** automatically on close. The file stays encrypted on disk.

🔍 **Observation**: an ergonomic workflow for daily changes: no need for manual `decrypt` then `encrypt`.

## 📚 Exercise 4 — Run the playbook with decryption

Create `playbook.yml` at the lab root: it consumes `secret.yml` via
`vars_files:`, without ever decrypting it on disk.

```bash
cat > playbook.yml <<'EOF'
---
- name: "Démonstration Ansible Vault : fichier chiffré"
  hosts: web1.lab
  become: true
  gather_facts: false

  vars_files:
    - secret.yml          # fichier chiffré, déchiffré au runtime

  tasks:
    - name: Afficher que les variables sont disponibles
      ansible.builtin.copy:
        dest: /tmp/lab77-vault-test.txt
        content: |
          Lab 77 : vault déchiffrement OK
          db_password length: {{ db_password | length }}
          api_token starts: {{ api_token[:4] }}...
        mode: "0600"
      no_log: false       # pour la démo on ne masque pas
EOF

ansible-playbook playbook.yml --vault-password-file=.vault_password
```

Output:

```text
PLAY [Démonstration Ansible Vault : fichier chiffré] *********

TASK [Afficher que les variables sont disponibles] ***********
changed: [web1.lab]

PLAY RECAP ***************************************************
web1.lab : ok=1 changed=1 unreachable=0 failed=0
```

🔍 **Observation**: Ansible decrypts `secret.yml` **automatically** at runtime thanks to `vars_files: secret.yml`. The playbook uses `db_password` and `api_token` as normal variables.

## 📚 Exercise 5 — Check the result on web1.lab

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab "sudo cat /tmp/lab77-vault-test.txt"
```

Expected output:

```text
Lab 77 : vault déchiffrement OK
db_password length: 18
api_token starts: tok_...
```

## 📚 Exercise 6 — Re-encrypt with a new password

```bash
echo "NouveauMotDePasse2026!" > .vault_password_new
chmod 0600 .vault_password_new

ansible-vault rekey secret.yml \
  --vault-password-file=.vault_password \
  --new-vault-password-file=.vault_password_new

# Check that the old password no longer works
ansible-vault view secret.yml --vault-password-file=.vault_password
# → ERROR: Decryption failed
```

🔍 **Observation**: `rekey` lets you **rotate** the vault password without changing the content. Mandatory in case of a leak or the departure of a team member.

```bash
# Restore for the tests
ansible-vault rekey secret.yml \
  --vault-password-file=.vault_password_new \
  --new-vault-password-file=.vault_password
rm .vault_password_new
```

## 📚 Exercise 7 — Decrypt permanently (rare)

```bash
ansible-vault decrypt secret.yml --vault-password-file=.vault_password
cat secret.yml                  # the file is in cleartext!
```

🔍 **Observation**: `decrypt` **modifies the file on disk** (becomes cleartext). To be used **only for exceptional debugging**: otherwise you lose the protection. Re-encrypt afterwards:

```bash
ansible-vault encrypt secret.yml --vault-password-file=.vault_password
```

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must display `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) rather than the short name (`ansible-lint --profile
  production` checks this).
- **Targeting convention**: this lab targets db1.lab; to adapt it to another
  group, adjust `hosts:` in `playbook.yml`/`solution.yml` then run it again.
- **Isolated reset**: `dsoxlab clean <id-du-lab>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why can the encrypted file be committed to Git **safely**? What is the cryptographic guarantee?

2. What happens if you run the playbook **without** `--vault-password-file`? (Test: remove the option and observe)

3. How do you **detect** that a secret was committed in cleartext by accident? (Hint: `gitleaks`, `git-secrets`, `pre-commit detect-private-key`)

4. Why must the vault password have **`mode 0600`**?

5. How do you share a vault file with **several people** without sharing the password in cleartext? (Topic of lab 79: multi vault-id)

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to **use 2 encrypted files** (db_secrets.yml + api_secrets.yml) in a unified playbook on `db1.lab`. Automated tests via `pytest+testinfra` (5 tests).

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **`ansible-vault rekey` in CI/CD**: automate the periodic rotation of vault passwords.
- **Environment variables**: `ANSIBLE_VAULT_PASSWORD_FILE=.vault_password` avoids typing the option on every command.
- **Multi vault-id** (lab 79): a different password per environment (dev/staging/prod).
- **Inline variables encrypt_string** (lab 78): a more readable alternative to encrypting a complete file.
- **HashiCorp Vault integration** (lab 82): externalize secrets in an enterprise vault.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile=production playbook.yml
```

The linter checks:

- No cleartext secret in the playbook (`no-log-password`).
- FQCN on all modules (`ansible.builtin.copy`).
- Presence of `mode:` on the deposited files.
- No `command:` without `creates:` or `changed_when:`.
