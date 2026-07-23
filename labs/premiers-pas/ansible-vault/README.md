# Lab 04b — First steps with `ansible-vault`

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**First steps with Ansible Vault**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/premiers-pas-ansible-vault/)

As soon as a playbook handles a **password**, an **API token** or a
**private key**, you must encrypt these values before committing them into
Git. **`ansible-vault`** is the native Ansible mechanism: it encrypts YAML
files with **AES-256** using a vault password.

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961...
6136353338613232633836333261396531376630...
```

→ This blob is **safe to commit** to public GitHub: without the vault
password, the content is inaccessible.

| Workflow | Command |
| --- | --- |
| Encrypt an existing file | `ansible-vault encrypt secret.yml` |
| View without modifying | `ansible-vault view secret.yml` |
| Edit (auto decrypt/re-encrypt) | `ansible-vault edit secret.yml` |
| Decrypt (rare, debug) | `ansible-vault decrypt secret.yml` |
| Run a play that consumes it | `ansible-playbook play.yml --vault-password-file=.vault_password` |

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Create** a vault password in a `.vault_password` file.
2. **Encrypt** a YAML file with `ansible-vault encrypt`.
3. **View / edit** an encrypted file without decrypting it on disk.
4. **Run a playbook** that consumes an encrypted file via `vars_files:`.
5. Understand why `.vault_password` must be **mode `0600`** and
   **gitignored**.
6. Tell `--vault-password-file` (recommended) apart from `--ask-vault-pass`
   (interactive).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ansible.builtin.ping
ansible-vault --version
```

## ⚙️ Target tree layout

```text
labs/premiers-pas/ansible-vault/
├── README.md                        ← this file
├── .vault_password                  ← (to create, gitignored, mode 0600)
├── secret.yml                       ← (to create, then encrypt)
├── lab.yml                          ← (to write by following the exercises)
└── challenge/
    ├── README.md                    ← challenge brief
    └── tests/
        └── test_vault_basics.py
```

## 📚 Exercise 1 — Create the vault password

```bash
cd labs/premiers-pas/ansible-vault/

echo "premiers-pas-vault-2026" > .vault_password
chmod 0600 .vault_password
ls -la .vault_password
```

🔍 **Observation**: `mode 0600` (`-rw-------`) means **readable/writable
only by the owner**. Without it, `ansible-vault` may accept
the file but it is a major anti-pattern (other system users can steal the
password).

> ⚠️ **The `.vault_password` file must NEVER be committed into Git.**
> It is already covered by the repo's root `.gitignore`. Back it up
> in an external password manager (Bitwarden, 1Password).

## 📚 Exercise 2 — Create a plaintext secrets file

Create `secret.yml`:

```yaml
---
db_password: "Sup3rSecretP@ss2026!"
api_token: "tok_demo_abc123xyz789"
```

```bash
cat secret.yml         # plaintext content, readable
```

## 📚 Exercise 3 — Encrypt the file

```bash
ansible-vault encrypt secret.yml --vault-password-file=.vault_password
cat secret.yml | head -3
```

Output:

```text
$ANSIBLE_VAULT;1.1;AES256
63373766303831373034386637393762353961...
6136353338613232633836333261396531376630...
```

🔍 **Observation**: the file is **transformed in place**. The plaintext
content no longer exists on disk. Only `ansible-vault` (with the right
password) can read it back.

## 📚 Exercise 4 — View without modifying

```bash
ansible-vault view secret.yml --vault-password-file=.vault_password
```

Output:

```yaml
---
db_password: "Sup3rSecretP@ss2026!"
api_token: "tok_demo_abc123xyz789"
```

🔍 **Observation**: `view` decrypts **in memory** for display,
**without modifying** the file on disk. The file stays encrypted.

## 📚 Exercise 5 — Edit an encrypted file

```bash
ansible-vault edit secret.yml --vault-password-file=.vault_password
```

This command:

1. Decrypts the file **in memory**.
2. Opens your `$EDITOR` (vim/nano).
3. You edit normally (add for example `app_secret: "xyz"`).
4. On save, **re-encrypts automatically**.

The file on disk stays encrypted throughout.

🔍 **Observation**: an ergonomic workflow for daily edits: no need for
manual `decrypt` then `encrypt`.

## 📚 Exercise 6 — Write a playbook that consumes the secret

Create `lab.yml`:

```yaml
---
- name: Premiers pas vault — déposer un secret sur db1
  hosts: db1.lab
  become: true
  gather_facts: false
  vars_files:
    - secret.yml         # ← Ansible decrypts automatically at runtime

  tasks:
    - name: Déposer la config DB avec le mot de passe déchiffré
      ansible.builtin.copy:
        dest: /tmp/db-config.txt
        content: |
          # Lab 04b — vault déchiffrement OK
          db_password={{ db_password }}
          api_token={{ api_token }}
        owner: root
        group: root
        mode: "0600"
      no_log: true           # ← keyword at task level (not in the module)
```

🔍 **Observation**:

- `vars_files: [secret.yml]` loads the file, **encrypted or not**,
  Ansible detects the `$ANSIBLE_VAULT` header automatically.
- `no_log: true` prevents sensitive variables from being shown
  in the Ansible output (good practice with vault).
- `mode: "0600"` on the dropped file prevents other users from reading it.

## 📚 Exercise 7 — Run the playbook with decryption

```bash
ansible-playbook lab.yml --vault-password-file=.vault_password
```

Output:

```text
PLAY [Premiers pas vault — déposer un secret sur db1] ********

TASK [Déposer la config DB avec le mot de passe déchiffré] ***
changed: [db1.lab]

PLAY RECAP ***************************************************
db1.lab : ok=1 changed=1 unreachable=0 failed=0
```

🔍 **Observation**: Ansible decrypts `secret.yml` **in memory at
runtime**, never writing the plaintext content to disk. The
result on `db1.lab`:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab "sudo cat /tmp/db-config.txt"
```

Expected output:

```text
# Lab 04b — vault déchiffrement OK
db_password=Sup3rSecretP@ss2026!
api_token=tok_demo_abc123xyz789
```

## 📚 Exercise 8 — What happens without the password?

```bash
ansible-playbook lab.yml         # → WITHOUT --vault-password-file
```

Output:

```text
ERROR! Attempting to decrypt but no vault secrets found
```

🔍 **Observation**: Ansible **refuses to run** without the password.
**Secure by default**. For an interactive workflow:

```bash
ansible-playbook lab.yml --ask-vault-pass
```

You will be prompted to type the password on the keyboard (useful in a
demo, **not in CI/CD** where the file is more convenient).

## 🔍 Observations to note

- **Always** encrypt secrets files **before** the first
  Git commit.
- **`.vault_password`**: mode `0600`, **gitignored**, backed up
  elsewhere.
- **`vars_files: [secret.yml]`** is enough: Ansible detects the vault
  format automatically.
- **`no_log: true`** on tasks that handle secrets, otherwise
  they appear in `ansible-playbook -v`.
- **`--vault-password-file`** > `--ask-vault-pass` for CI/CD;
  the reverse in a demo.

## 🤔 Reflection questions

1. Why must `.vault_password` have `mode 0600`? What happens
   if I leave `0644`?

2. How do you **detect** that a secret was committed in plaintext by accident?
   (Hint: `gitleaks`, `git-secrets`, `pre-commit detect-private-key`.)

3. Imagine your `.vault_password` has leaked. What must you do, **in
   order**?

4. Why is `no_log: true` combined with vault in tasks that
   handle sensitive variables?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md).

## 💡 Going further

- **`ANSIBLE_VAULT_PASSWORD_FILE=.vault_password`**: an env variable that
  avoids repeating `--vault-password-file` on every command.
- **Inline `!vault` variable** (lab 78): an alternative to encrypt
  **a single variable** instead of a whole file.
- **Multi vault-id** (lab 79): a different password per
  environment (dev/staging/prod).
- **Vault in a role** (lab 81): `defaults/main.yml` (plaintext) +
  `vars/main.yml` (encrypted).
- **HashiCorp Vault / OpenBao integration** (labs 82-83): externalize
  secrets into an enterprise vault.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/premiers-pas/ansible-vault/lab.yml
ansible-lint labs/premiers-pas/ansible-vault/challenge/solution.yml
ansible-lint --profile production labs/premiers-pas/ansible-vault/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your
code follows best practices: explicit FQCN, `name:` on
every task, file modes as strings, idempotence respected, deprecated modules
avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce
> anti-patterns.
