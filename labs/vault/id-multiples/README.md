# Lab 79 — Multiple Vault IDs (dev / prod / staging)

> 💡 **Prerequisite**: `ansible all -m ansible.builtin.ping` replies `pong` on the 4 VMs.

## 🧠 Recap

🔗 [**Multiple Vault IDs**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-id-multiples/)

**A single vault password** is not enough in a team: everyone has access to the **prod** secrets if they can decrypt **dev**. Solution: **vault-ids labeled** by environment.

```yaml
$ANSIBLE_VAULT;1.2;AES256;dev      ← header with the "dev" label
$ANSIBLE_VAULT;1.2;AES256;prod     ← header with the "prod" label
```

Each file carries its **label**. At runtime, you pass **several `--vault-id`**:

```bash
ansible-playbook \
  --vault-id dev@.vault_password_dev \
  --vault-id prod@.vault_password_prod \
  playbook.yml
```

Ansible tries each vault-id on each encrypted file and uses the right one. **Team workflow**: the devs only have `.vault_password_dev`, the ops have both.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Encrypt with a **labeled vault-id** (`--encrypt-vault-id dev`).
2. Decrypt **several vault-ids** in the same run.
3. Structure `inventory/group_vars/<env>/secrets.yml` per environment.
4. Understand the **v1.2 header** (`$ANSIBLE_VAULT;1.2;AES256;<label>`).
5. **Team workflow**: one password per environment, distributed according to roles.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/vault/id-multiples/
ls -la                              # 2 fichiers .vault_password_*
ls inventory/group_vars/            # dev/  prod/
```

## ⚙️ Target tree

```text
labs/vault/id-multiples/
├── README.md
├── .vault_password_dev             ← DEV password
├── .vault_password_prod            ← PROD password
├── inventory/
│   ├── hosts.yml                   ← 2 groups: dev, prod
│   └── group_vars/
│       ├── dev/
│       │   └── secrets.yml         ← encrypted with vault-id "dev"
│       └── prod/
│           └── secrets.yml         ← encrypted with vault-id "prod"
├── playbook.yml
└── challenge/
    ├── solution.yml
    └── tests/
        └── test_vault_ids.py
```

## 📚 Exercise 1 — Inspect the vault-id headers

```bash
head -1 inventory/group_vars/dev/secrets.yml
# → $ANSIBLE_VAULT;1.2;AES256;dev

head -1 inventory/group_vars/prod/secrets.yml
# → $ANSIBLE_VAULT;1.2;AES256;prod
```

🔍 **Observation**: the **version 1.2** of the vault format includes the **label** in the header. Version 1.1 (labs 77/78) does not. The label lets Ansible **know which password to use** for each file.

## 📚 Exercise 2 — View a vault-id file

```bash
ansible-vault view \
  --vault-id dev@.vault_password_dev \
  inventory/group_vars/dev/secrets.yml
```

Output:

```yaml
db_host: dev-db.example.com
db_password: "DevDBPass123"
```

🔍 **Observation**: without **`dev@`**, Ansible tries all the `--vault-id` until it finds the right one. With the explicit label, resolution is **immediate**, useful when debugging.

## 📚 Exercise 3 — Test the dev/prod isolation

```bash
# Try to decrypt the prod file with the DEV password
ansible-vault view \
  --vault-id dev@.vault_password_dev \
  inventory/group_vars/prod/secrets.yml
```

**Result**: FAILURE (`Decryption failed`). The dev password **does not decrypt** prod.

🔍 **Observation**: this is exactly the benefit of this isolation. A compromised dev does **not** give access to the prod secrets.

## 📚 Exercise 4 — Run the playbook with the 2 vault-ids

```bash
ansible-playbook -i inventory/hosts.yml \
  --vault-id dev@.vault_password_dev \
  --vault-id prod@.vault_password_prod \
  playbook.yml
```

Output:

```text
PLAY [Démo vault-id multiples] *********

TASK [Pose un fichier...] ***********
changed: [web1.lab]
changed: [db1.lab]

PLAY RECAP **************************
db1.lab  : ok=1 changed=1 unreachable=0 failed=0
web1.lab : ok=1 changed=1 unreachable=0 failed=0
```

🔍 **Observation**: `web1.lab` receives the DEV secrets (dev group), `db1.lab` receives the PROD secrets (prod group). **A single run** decrypts both environments using the right password for each.

## 📚 Exercise 5 — Check the deposited files

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab "sudo cat /tmp/lab79-web1.lab.txt"
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab  "sudo cat /tmp/lab79-db1.lab.txt"
```

`web1` sees `dev-db.example.com`, `db1` sees `prod-db.example.com`. **No leak** between environments.

## 📚 Exercise 6 — Re-encrypt a single environment

```bash
echo "NouveauMotDePasseDev2026" > .vault_password_dev_new
chmod 0600 .vault_password_dev_new

ansible-vault rekey \
  --vault-id dev@.vault_password_dev \
  --new-vault-id dev@.vault_password_dev_new \
  inventory/group_vars/dev/secrets.yml

# prod is NOT impacted!
ansible-vault view \
  --vault-id prod@.vault_password_prod \
  inventory/group_vars/prod/secrets.yml
# → toujours OK
```

🔍 **Observation**: rotating the DEV password **does not impact** PROD. Convenient to **rotate the dev secrets regularly** without disturbing prod.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must display `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) rather than the short name (`ansible-lint --profile
  production` checks this).
- **Targeting convention**: this lab targets db1.lab and web1.lab (two environments); to adapt it to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then run it again.
- **Isolated reset**: `dsoxlab clean <id-du-lab>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. What is the concrete risk of a single vault password shared between dev and prod?

2. If a team has 5 environments (dev, qa, staging, preprod, prod), does it need **5 vault-ids**?

3. How do you **distribute** the `.vault_password_*` files to the team? (Hint: HashiCorp Vault, OpenBao, enterprise secret managers)

4. What happens if you forget `--vault-id prod@...`? (Test: remove it and observe)

## 🚀 Final challenge

The challenge ([`challenge/`](challenge/)) proves that both environments are decrypted correctly with their respective passwords. Automated tests via `pytest+testinfra` (5 tests, including a check that the passwords have **different lengths**, proof of separate decryption).

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **`vault_identity_list`** in `ansible.cfg` to set the default vault-ids without passing them on the CLI.
- **Hybrid playbook**: vault-id `dev` AND vault-id `prod` variables in the same file (rare but possible).
- **CI/CD**: env variables `ANSIBLE_VAULT_PASSWORD_FILE_DEV` + `..._PROD` injected by GitHub/GitLab secrets.
- **Lab 82**: externalize into HashiCorp Vault instead of `.vault_password_*` files.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile=production .
```

The linter does not touch the `--vault-id`: it checks the classic Ansible code.
