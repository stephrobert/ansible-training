# Lab 80 — Mixed playbooks: main.yml + vault.yml per group

> 💡 **Prerequisite**: `ansible all -m ansible.builtin.ping` replies `pong` on the 4 VMs.

## 🧠 Recap

🔗 [**Mixed playbooks (cleartext + encrypted)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/playbooks-mixtes/)

**Recommended 2026 pattern**: separate the **public variables** (cleartext) from the **secrets** (encrypted) into two distinct files inside each `group_vars/<group>/`:

```text
inventory/group_vars/
├── all/
│   ├── main.yml        ← shared public variables (port, version, env)
│   └── vault.yml       ← shared secrets (encrypted)
├── webservers/
│   ├── main.yml        ← webservers public config
│   └── vault.yml       ← webservers secrets (encrypted)
└── dbservers/
    ├── main.yml
    └── vault.yml
```

**Naming convention**: prefix the vault variables with **`vault_*`** (e.g. `vault_admin_token`, `vault_db_password`). Allows a quick glance to distinguish a sensitive variable.

**Advantages**:

- **Readable Git diffs** on the public variables (`main.yml` changes often, `vault.yml` rarely).
- **Reading main.yml without decrypting**: no need for the vault password to understand the config.
- **Isolated secrets**: a single file to protect per group.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Structure **`group_vars/<group>/main.yml + vault.yml`**.
2. **Encrypt only the secrets**, not the public configurations.
3. Adopt the **`vault_*`** convention for the sensitive variables.
4. See Ansible **merge automatically** main.yml and vault.yml (same global variable).
5. **Reference** the vault_* from the playbook as normal variables.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/vault/playbooks-mixtes/
ls inventory/group_vars/all/        # main.yml + vault.yml
ls inventory/group_vars/webservers/ # main.yml + vault.yml
```

## ⚙️ Target tree

```text
labs/vault/playbooks-mixtes/
├── README.md
├── .vault_password                 ← single vault password (mode 0600)
├── inventory/
│   ├── hosts.yml
│   └── group_vars/
│       ├── all/
│       │   ├── main.yml            ← deployment_environment (cleartext)
│       │   └── vault.yml           ← vault_admin_token (encrypted)
│       └── webservers/
│           ├── main.yml            ← http_port, worker_count (cleartext)
│           └── vault.yml           ← vault_web_secret, vault_web_db_password (encrypted)
├── playbook.yml
└── challenge/
    ├── solution.yml
    └── tests/
```

## 📚 Exercise 1 — Inspect the mixed structure

```bash
cat inventory/group_vars/all/main.yml
# → deployment_environment: lab80 (cleartext)

cat inventory/group_vars/all/vault.yml | head -3
# → $ANSIBLE_VAULT;1.1;AES256 (encrypted)
```

🔍 **Observation**: the **2 files** are **merged** automatically by Ansible: a host of the `all` group sees **all** the variables (cleartext + encrypted) as a single namespace.

## 📚 Exercise 2 — Run the playbook

```bash
ansible-playbook -i inventory/hosts.yml \
  --vault-password-file=.vault_password \
  playbook.yml
```

Output: `changed=1` on web1.lab. The playbook accesses 5 variables (3 cleartext, 3 encrypted) **without distinction** in the `{{ var }}`.

## 📚 Exercise 3 — Check the result

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab "sudo cat /tmp/lab80-mixte.txt"
```

Output:

```text
=== Lab 80 — playbook mixte ===

Variables PUBLIQUES (group_vars/<group>/main.yml) :
  deployment_environment: lab80
  http_port: 80
  worker_count: 4

Secrets CHIFFRÉS (group_vars/<group>/vault.yml) :
  vault_admin_token starts: lab80
  vault_web_secret starts: web_s
  vault_web_db_password length: 17
```

🔍 **Observation**: the 6 variables are accessible transparently. The **`vault_*` prefix** lets you distinguish **visually** in the code the sensitive values.

## 📚 Exercise 4 — Read main.yml WITHOUT decrypting

```bash
cat inventory/group_vars/webservers/main.yml
# → http_port, worker_count visible
```

🔍 **Crucial observation**: a **developer without the vault password** can read main.yml and understand the config (ports, versions). This is exactly the benefit of the pattern: **separation of public reading / sensitive reading**.

## 📚 Exercise 5 — Typical Git diff

Change the http port:

```bash
sed -i 's/http_port: 80/http_port: 8080/' inventory/group_vars/webservers/main.yml
git diff
```

A **readable and clear** Git diff. With a fully encrypted file, the diff would be **incomprehensible** (just random hex changes).

```bash
# Restore
sed -i 's/http_port: 8080/http_port: 80/' inventory/group_vars/webservers/main.yml
```

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must display `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) rather than the short name (`ansible-lint --profile
  production` checks this).
- **Targeting convention**: this lab targets web1.lab; to adapt it to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then run it again.
- **Isolated reset**: `dsoxlab clean <id-du-lab>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why prefix the sensitive variables with **`vault_*`** rather than with `_secret_*` or something else?

2. What happens if **`main.yml`** and **`vault.yml`** define the same variable? (Test: add `vault_admin_token: clair` in main.yml)

3. How do you **rotate ONLY** the secrets of `webservers/` without touching `all/vault.yml`?

4. Why **separate** by group (`all/`, `webservers/`) rather than everything in `all/`?

## 🚀 Final challenge

The challenge ([`challenge/solution.yml`](challenge/solution.yml)) deploys on webservers and proves that the main.yml + vault.yml variables merge correctly. Automated tests (4 tests).

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Pattern in roles** (lab 81): `defaults/main.yml` + `vars/vault.yml` of the role.
- **Multi vault-id** (lab 79): apply this pattern per environment (dev/prod).
- **gitignore .vault_password**: `.vault_password*` in the repo root `.gitignore` (the password must NEVER be committed).
- **`ansible.cfg [defaults] vault_password_file`** to set the default password without `--vault-password-file` on every command.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile=production .
```

The linter **does not touch** the vault files. It checks the classic Ansible code (FQCN, mode, no_log).
