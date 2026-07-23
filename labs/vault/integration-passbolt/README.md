# Lab 83 — Passbolt integration (OpenPGP team manager)

> 💡 **Prerequisites**:
> - Podman installed.
> - Collection `anatomicjc.passbolt`: `ansible-galaxy collection install anatomicjc.passbolt`.
> - Python module `py-passbolt`: `pip install py-passbolt` (or `pipx inject ansible py-passbolt`).
> - GnuPG (`gpg`) to generate the user's OpenPGP key.

## 🧠 Recap

🔗 [**Passbolt integration with Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-passbolt/)

**Passbolt** is a **team-oriented** password manager under an open-source license (AGPL). Unlike HashiCorp Vault (lab 82), it aims at a different audience:

| Aspect | HashiCorp Vault / OpenBao | Passbolt |
|--------|---------------------------|----------|
| **Use case** | Infra secrets, dynamic secrets, CI/CD | Team passwords (humans + machines) |
| **Model** | Token / AppRole / IAM | OpenPGP key per user |
| **Audit** | Native lease + audit log | Activity log + email notifications |
| **UI** | Optional (CLI-first) | Rich web UI (browser + extension) |
| **Sharing** | HCL policies | Groups + roles + permissions per resource |
| **Rotation** | Automatic (dynamic secrets) | Manual (UI) |

**When to choose Passbolt?** When the human team must **share passwords** (db admin, SaaS accounts, certificates, third-party API keys) and you want a workflow accessible to **non-DevOps** (reading by marketing, support, etc.) while keeping Ansible able to retrieve these secrets on the infrastructure side.

**When to keep HashiCorp Vault?** For **dynamic** secrets, **X.509 PKI certificates**, **dynamic database credentials**, the needs for **automatic TTL** and **Cloud IAM** integration.

⚠️ **Not redundant** with Vault: the two tools answer **complementary** needs. Many organizations use **both** (Passbolt for humans, Vault for infra).

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Start** a local Passbolt CE (Podman + MariaDB).
2. Understand **OpenPGP** authentication (private key + passphrase).
3. **Retrieve** a Passbolt secret from Ansible with the **`anatomicjc.passbolt`** collection.
4. Compare **Passbolt** and **HashiCorp Vault** on concrete cases.
5. **Secure** the OpenPGP private key (no Git commit).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/vault/integration-passbolt/

# Install the Passbolt collection
ansible-galaxy collection install anatomicjc.passbolt

# Install py-passbolt (Python client)
pipx inject ansible py-passbolt

# Start local Passbolt
./setup-passbolt.sh
```

## ⚙️ Target tree

```text
labs/vault/integration-passbolt/
├── README.md
├── setup-passbolt.sh                ← starts Passbolt + MariaDB in containers
├── .passbolt-private.asc            ← your exported private key (gitignored)
└── challenge/
    ├── README.md                    ← challenge contract
    ├── solution.yml                 ← to write: lookup anatomicjc.passbolt
    └── tests/
        └── test_functional.py       ← tests against the running Passbolt
```

## 📚 Exercise 1 — Start local Passbolt

```bash
./setup-passbolt.sh
```

Typical output:

```text
[setup-passbolt] Création du réseau passbolt-lab83...
[setup-passbolt] Démarrage MariaDB...
[setup-passbolt] Démarrage Passbolt CE...
[setup-passbolt] Initialisation admin user...

[setup-passbolt] OK — Passbolt disponible sur https://localhost:8443
```

🔍 **Observation**: Passbolt = **2 containers** (DB + app). An architecture close to a classic Rails/Django app. No HA cluster included in the CE version.

## 📚 Exercise 2 — Complete the registration via the UI

The `register_user` command returns a **unique registration link**. The registration is done in the browser because it requires the **generation of an OpenPGP key** on the client side (never transmitted to the server).

```text
1. Open https://localhost:8443 (accept the self-signed)
2. Click the registration link returned by register_user
3. Choose a strong passphrase (it will be asked on every decryption)
4. The Passbolt extension generates the GPG key in the browser
5. DOWNLOAD the recovery file (kit), IRRECOVERABLE otherwise
```

🔍 **Crucial observation**: the **private key** **never** leaves the user's browser. The server only stores the **public key**. If you lose the private key + the recovery kit → **secrets lost forever**. This is a **major difference** with Vault (where the server has "everything").

## 📚 Exercise 3 — Export the private key for Ansible

For Ansible to use Passbolt, we need the private key of a dedicated user (recommended pattern: create an `ansible@lab83.local` user separate from `admin@`).

```bash
# Create a dedicated Ansible user
podman exec passbolt-app-lab83 su -m -c \
  "/usr/share/php/passbolt/bin/cake passbolt register_user \
    -u ansible@lab83.local -f Ansible -l Bot -r user" www-data

# Complete the registration via the UI, then export its private key:
mkdir -p .passbolt
# (export GPG from the browser → paste into .passbolt/private.key)
chmod 600 .passbolt/private.key

# .gitignore mandatory:
echo ".passbolt/" >> ../../.gitignore
```

🔍 **Observation**: a **dedicated** Ansible user simplifies auditing (who accessed: Ansible vs a human). Limited permissions on the "Infrastructure" groups only.

## 📚 Exercise 4 — Store a demo secret in Passbolt

Via the UI:

```text
1. Log in as admin@lab83.local
2. New password → name=lab83-demo, password=DemoPassbolt2026!
3. Share with ansible@lab83.local (read only)
```

Via the REST API (for automation, more advanced): see the [`anatomicjc.passbolt`](https://galaxy.ansible.com/ui/repo/published/anatomicjc/passbolt/) collection.

🔍 **Observation**: **explicit sharing** per resource. Ansible sees **only** the secrets explicitly shared with it. A **least-privilege** pattern by construction.

## 📚 Exercise 5 — Lookup from Ansible

Write the challenge playbook (cf. [`challenge/README.md`](challenge/README.md)),
then:

```bash
export PASSBOLT_URL=https://localhost:8443
export PASSBOLT_PASSPHRASE="votre-passphrase"

ansible-playbook challenge/solution.yml
```

Output:

```text
TASK [Récupérer le secret 'lab83-demo' depuis Passbolt] ***
ok: [localhost]

TASK [Afficher uniquement la longueur du secret] ***
ok: [localhost] => 
  msg: "Secret length: 19"
```

🔍 **Observation**: `no_log: true` on the `set_fact` to **never** log the cleartext value. The final `debug` only exposes the length.

## 📚 Exercise 6 — When Passbolt complements Ansible Vault

A realistic pattern: **Passbolt** stores the Ansible Vault **password**.

```bash
# 1. The admin stores "ansible-vault-master-password" in Passbolt
# 2. The CI pipeline retrieves this password via a Passbolt lookup
# 3. The pipeline decrypts the Ansible Vault files with this password
# 4. Ansible runs the playbooks
```

🔍 **Observation**: a **chain of trust**. Passbolt protects the **master password**, which protects the **vault files**. Simple rotation: change the vault password → re-encrypt → update in Passbolt.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must display `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) rather than the short name (`ansible-lint --profile
  production` checks this).
- **Targeting convention**: this lab targets db1.lab + a Passbolt instance; to adapt it to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then run it again.
- **Isolated reset**: `dsoxlab clean <id-du-lab>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why **Passbolt** rather than a `pass(1)` GPG vault shared via Git?

2. What happens if the Ansible **recovery kit** is lost and the passphrase is forgotten?

3. How do you **rotate** a password stored in Passbolt without breaking the running playbooks?

4. **Passbolt vs HashiCorp Vault**: for an SSH Bastion shared between 5 admins, which one to choose? Why?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) requires a running Passbolt,
your exported OpenPGP key and the passphrase in the environment:
the tests replay your playbook and check the deposited proof (mode
`0600`, consistent length, no cleartext secret in the YAML). As long as
the infrastructure is missing, they go into an explicit `skip`.

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Passbolt PRO**: SSO (SAML, OIDC), MFA, advanced audit logs, teams.
- **Self-hosted in prod**: Passbolt Helm chart (K8s) or the official Ansible role `passbolt.passbolt_collection`.
- **REST API + JWT**: an alternative to OpenPGP for machine-to-machine integrations (Passbolt 4.x+).
- **Browser extension**: auto-fills the web forms (a differentiator vs Vault).
- **Winning combo**: Passbolt (humans) + HashiCorp Vault (infra/dynamic) + Ansible Vault (versioned sensitive configs).

## 🔍 Security — 2026 best practices

- **OpenPGP private key**: `chmod 600`, never committed, ideally in a keystore (gnome-keyring, macOS Keychain).
- **Passphrase**: passed via an env variable, never on the CLI (`ps aux` would reveal it).
- **Valid TLS** in prod (Let's Encrypt). The self-signed of the lab is only for local dev.
- **MFA** on all human accounts (free TOTP in CE).
- **Audit log enabled** (Passbolt 4.5+): who accessed which secret, when, from which IP.
- **Database backup**: the MariaDB DB contains encrypted secrets + public keys. Not sufficient on its own, each user must also back up their **private key + recovery kit**.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/vault/integration-passbolt/lab.yml
ansible-lint labs/vault/integration-passbolt/challenge/solution.yml
ansible-lint --profile production labs/vault/integration-passbolt/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
