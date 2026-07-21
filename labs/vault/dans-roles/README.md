# Lab 81 — Vault in a role (cleartext defaults + encrypted vars)

> 💡 **Prerequisite**: `ansible all -m ansible.builtin.ping` replies `pong` on the 4 VMs.

## 🧠 Recap

🔗 [**Vault in roles**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-dans-roles/)

An Ansible role can contain its **own secrets**, encrypted with Vault. The **standard 2026 pattern**:

```text
roles/secured_app/
├── defaults/
│   └── main.yml            ← PUBLIC overridable variables (cleartext)
│                              reference the vault_* via indirect Jinja
├── vars/
│   └── main.yml            ← ENCRYPTED secrets (vault_*)
└── tasks/
    └── main.yml            ← uses the public variables
```

**Indirection pattern**: `defaults/main.yml` exposes `secured_app_db_password` (cleartext) which points to `vault_secured_app_db_password` (encrypted in `vars/`) via Jinja:

```yaml
# defaults/main.yml (clair)
secured_app_db_password: "{{ vault_secured_app_db_password }}"
```

```yaml
# vars/main.yml (CHIFFRÉ)
vault_secured_app_db_password: "RoleDBPasswordLab81!"
```

The user of the role can **override** `secured_app_db_password` in their playbook (high priority) without having to decrypt/modify `vars/main.yml`. **Best of both worlds**: distributed secrets, override possible.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Structure **`defaults/main.yml` + encrypted `vars/main.yml`** in a role.
2. Use the **indirection pattern** `secured_app_X = vault_secured_app_X`.
3. Understand why **`vars/main.yml`** (priority 15) is a good place for secrets.
4. **Override** a defaults/ variable from the user playbook.
5. Naming convention **`vault_<role>_<var>`**.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/vault/dans-roles/
tree roles/secured_app/
cat roles/secured_app/defaults/main.yml
ansible-vault view roles/secured_app/vars/main.yml --vault-password-file=.vault_password
```

## ⚙️ Target tree

```text
labs/vault/dans-roles/
├── README.md
├── .vault_password                    ← vault password (mode 0600)
├── playbook.yml                       ← consumes the role
└── roles/
    └── secured_app/
        ├── defaults/main.yml          ← public variables (CLEARTEXT)
        ├── vars/main.yml              ← secrets (ENCRYPTED vault)
        ├── tasks/main.yml             ← role logic
        └── meta/main.yml              ← metadata
```

## 📚 Exercise 1 — Inspect the indirection pattern

```bash
cat roles/secured_app/defaults/main.yml
```

Output:

```yaml
secured_app_user: appuser                                              # ← clair
secured_app_db_password: "{{ vault_secured_app_db_password }}"         # ← indirection
secured_app_api_token: "{{ vault_secured_app_api_token }}"
```

🔍 **Observation**: `defaults/main.yml` contains **no cleartext secret**. It **points** to the `vault_*` variables that are encrypted in `vars/main.yml`.

## 📚 Exercise 2 — See the encrypted content

```bash
ansible-vault view roles/secured_app/vars/main.yml --vault-password-file=.vault_password
```

Output:

```yaml
vault_secured_app_db_password: "RoleDBPasswordLab81!"
vault_secured_app_api_token: "role_api_tok_lab81_xyz"
```

🔍 **Observation**: `vars/main.yml` contains the **real values**, encrypted. The `vault_*` prefix is a convention to distinguish these internal variables.

## 📚 Exercise 3 — Run the playbook

```bash
ansible-playbook --vault-password-file=.vault_password \
  -e "ansible_roles_path=./roles" \
  playbook.yml
```

Output: `changed=1` on web1.lab. The role decrypted and used the secrets.

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab "sudo cat /tmp/lab81-secured-app.txt"
```

## 📚 Exercise 4 — Override a defaults/ variable

In `playbook.yml`, add:

```yaml
- name: Démo override
  hosts: web1.lab
  roles:
    - role: secured_app
      vars:
        secured_app_port: 12345
```

🔍 **Observation**: `secured_app_port` is overridden without touching the role. **`secured_app_db_password`** (which points to `vault_*`) **cannot** be overridden as easily (`vault_*` is in `vars/main.yml` priority 15).

## 📚 Exercise 5 — Why vars/ and not defaults/ for the secret?

If we put `vault_secured_app_db_password` in `defaults/main.yml` (priority 2), a user could **override it silently** from their playbook (priority 12), a leak risk if the override value is poorly managed.

By putting it in `vars/main.yml` (priority 15), a play `vars:` (12) cannot override it; `--extra-vars` (22) and a role param (20) can, an **explicit and controlled** behavior.

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

1. Why the **indirection pattern** (cleartext defaults → encrypted vars) rather than everything directly in `vars/`?

2. How do you **rotate** `vault_secured_app_db_password` without breaking the role for the users?

3. If a user wants to **override** the password on the CLI, how do they do it? (Hint: `--extra-vars` priority 22)

4. Why the **`vault_<role>_<var>` convention**? What happens if 2 roles use `vault_db_password`?

## 🚀 Final challenge

The challenge ([`challenge/solution.yml`](challenge/solution.yml)) deploys on `db1.lab` with an override of `secured_app_port: 9999`. Automated tests (5 tests including a check that the vault secrets are correctly decrypted).

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Encrypted `vars/<distro>.yml`**: different secrets per OS (mandatory, rare).
- **Multi vault-id in a role**: one password per environment even within the role.
- **Externalize into HashiCorp Vault** (lab 82): avoid storing secrets in the repo.
- **Passbolt** (lab 83): a team-friendly alternative for team secrets.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint --profile=production roles/
```

The linter checks the pattern (FQCN, no_log if needed). It does not touch the vault secrets.
