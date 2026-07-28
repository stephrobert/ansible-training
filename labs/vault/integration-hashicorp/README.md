# Lab 82 — HashiCorp Vault / OpenBao integration

> 💡 **Prerequisites**:
> - Podman or Docker installed.
> - Collection `community.hashi_vault`: `ansible-galaxy collection install community.hashi_vault`.
> - The Python module `hvac`: `pip install hvac` (or `pipx inject ansible hvac`).

## 🧠 Recap

🔗 [**HashiCorp Vault / OpenBao with Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/integration-hashicorp-vault/)

**Limits of Ansible Vault** (labs 77-81):

- Vault password stored somewhere (file, env var), a human risk.
- No **centralized rotation** of secrets.
- No detailed **audit logs** (who accessed which secret when).
- No **leases** or TTL on the secrets.

**HashiCorp Vault** (and its open-source fork **OpenBao**) solve these problems: centralization, rotation, audit, TTL, Cloud integrations (AWS IAM, Azure AD, K8s service accounts).

**Almost identical API** between HashiCorp Vault and OpenBao: the same Ansible playbook works with both. Choice depends on context:

- **HashiCorp Vault**: BSL license (commercial beyond a threshold), enterprise features.
- **OpenBao**: 100% open-source fork (MPL-2.0), Linux Foundation governance.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Start** a local Vault in dev mode (Docker/Podman).
2. **Store** a secret via `vault kv put`.
3. **Retrieve** the secret from Ansible with **`community.hashi_vault.vault_kv2_get`**.
4. Understand the **difference** between `vault_kv1_get` and `vault_kv2_get`.
5. **Authentication**: token, AppRole, JWT, Kubernetes.
6. **CI/CD workflow**: use Vault to avoid storing secrets in Git.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/vault/integration-hashicorp/

# Installer hvac (client Python Vault)
pipx inject ansible hvac

# hvac and the collection are declared by the repository: nothing to install by hand
mise install                       # hvac ships with ansible-core (mise.toml)
ansible-galaxy collection install -r $ANSIBLE_TRAINING/requirements.yml

# Starting Vault is dsoxlab's job
dsoxlab run vault-integration-hashicorp
```

The server is declared in `runtime.services` of `lab.yaml`: `dsoxlab run` starts
it, waits until it answers, seeds `secret/lab82`, and `dsoxlab clean` stops it.
It listens on **8201**, not the default 8200, so it can coexist with another
Vault already running on the machine.

For OpenBao, change the service's `image:` in `lab.yaml`.

## ⚙️ Target tree

```text
labs/vault/integration-hashicorp/
├── README.md
├── lab.yaml                      ← declares the Vault service (image, port, secrets)
└── challenge/
    ├── README.md                 ← challenge contract
    ├── solution.yml              ← to write: lookup vault_kv2_get + proof
    └── tests/
        └── test_functional.py    ← tests against the running Vault
```

## 📚 Exercise 1 — Start a local Vault

```bash
dsoxlab run vault-integration-hashicorp
```

The lab declares its server, dsoxlab runs it:

```yaml
services:
  - name: vault
    image: hashicorp/vault:1.21
    ports: ["8201:8200"]          # 8201 on the host: 8200 is often taken
    ready_exec: vault status      # wait until it ANSWERS, not until the port opens
    post_start:
      - vault kv put secret/lab82 db_password=… api_key=…
```

Result: `http://127.0.0.1:8201`, the lab's dev token, and the secrets under
`secret/lab82`. Nothing to export — the playbook defaults to the same values.

🔍 **Observation**: Vault dev mode = **not secure** (no TLS, no seal, static root token). **Strictly** for local development. In prod: Vault HA + TLS + auto-unseal.

## 📚 Exercise 2 — Store secrets in Vault

```bash
# The service's post_start has already created secret/lab82
docker exec dsoxlab-ansible-training-vault vault kv get secret/lab82

# To add a secret manually:
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault kv put secret/lab82-app \
    db_url=postgres://... \
    db_password=DemoPass123
```

🔍 **Observation**: `kv v2` automatically versions the secrets (history, rollback). `kv v1` is the legacy mode (without versioning).

## 📚 Exercise 3 — Lookup from Ansible

Write the challenge playbook (cf. [`challenge/README.md`](challenge/README.md)),
then:

```bash
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=lab82-root

ansible-playbook challenge/solution.yml
```

Output:

```text
TASK [debug] **************
ok: [localhost] =>
  msg: "DB password length: 14"

PLAY RECAP ****************
localhost : ok=2 changed=1 unreachable=0 failed=0
```

🔍 **Observation**: the playbook **contains no cleartext secret**. The `lookup` retrieves the secret at runtime from Vault. Vault audit logs track who accessed it.

## 📚 Exercise 4 — AppRole authentication (production)

In prod, **we do not use the root token**. Recommended pattern: **AppRole**.

```bash
# Activer AppRole
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault vault auth enable approle

# Créer une policy "ansible-readonly"
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault sh -c '
  cat << EOF | vault policy write ansible-readonly -
path "secret/data/lab82" {
  capabilities = ["read"]
}
EOF
'

# Créer un AppRole
docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault write auth/approle/role/ansible-app \
    token_policies="ansible-readonly" \
    token_ttl=1h \
    token_max_ttl=4h

# Récupérer role_id et secret_id
ROLE_ID=$(docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault read -field=role_id auth/approle/role/ansible-app/role-id)
SECRET_ID=$(docker exec -e VAULT_TOKEN=lab82-root dsoxlab-ansible-training-vault \
  vault write -field=secret_id -f auth/approle/role/ansible-app/secret-id)

echo "role_id=$ROLE_ID, secret_id=$SECRET_ID"
```

The playbook then uses `auth_method: approle`:

```yaml
- name: Lookup avec AppRole
  vars:
    db_password: "{{ lookup('community.hashi_vault.vault_kv2_get',
                            'lab82',
                            engine_mount_point='secret',
                            url=vault_url,
                            auth_method='approle',
                            role_id=role_id,
                            secret_id=secret_id).secret.db_password }}"
```

🔍 **Observation**: the `secret_id` can be **ephemeral** (short TTL). The `role_id` is **public** (can be committed). Recommended pattern in CI/CD.

## 📚 Exercise 5 — Differences HashiCorp Vault vs OpenBao

Run the same playbook with **OpenBao**:

```bash
dsoxlab clean vault-integration-hashicorp
# Change the service image in lab.yaml to openbao/openbao:latest, then:
dsoxlab clean vault-integration-hashicorp && dsoxlab run vault-integration-hashicorp

# The playbook works IDENTICALLY
ansible-playbook challenge/solution.yml
```

🔍 **Observation**: no modification of the playbook. **Compatible API**. Choose Vault or OpenBao based on licensing, not on features (95% identical).

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must display `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) rather than the short name (`ansible-lint --profile
  production` checks this).
- **Targeting convention**: this lab targets db1.lab + a HashiCorp Vault server; to adapt it to another
  group, adjust `hosts:` in `lab.yml`/`solution.yml` then run it again.
- **Isolated reset**: `dsoxlab clean <id-du-lab>` at the lab root cleanly uninstalls
  what the solution set up so you can replay the scenario.

## 🤔 Reflection questions

1. Why **Vault > Ansible Vault file** in production?

2. What is the **concrete difference** between HashiCorp Vault and OpenBao in 2026?

3. Why **AppRole** rather than **root token** in CI/CD? What happens if the root token leaks?

4. What is a **secret lease** in Vault? How should Ansible manage the leases?

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) requires a running
Vault: the tests read the secrets via the API and check that the
proof deposited by your playbook matches (exact lengths, no
cleartext secret, idempotence). Without a server, they `skip`.

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Kubernetes auth**: Vault integrates with K8s service accounts for auto rotation.
- **AWS IAM / Azure AD / GCP auth**: no credentials to store.
- **Dynamic secrets**: Vault generates ephemeral DB credentials (PostgreSQL, MySQL, MongoDB).
- **Vault + Ansible Tower / AAP**: integrated Vault Credential Type.
- **Lab 83**: a team-friendly alternative with Passbolt (a team password manager).

## 🔍 Security — 2026 best practices

- **No token in cleartext** in `playbook.yml`, always via env vars (`VAULT_TOKEN`).
- **AppRole** in CI/CD with an ephemeral `secret_id` (renewed per job).
- **Mandatory TLS** in production (`https://`, pinned certificate).
- **Audit log** enabled on all prod Vaults (`vault audit enable file file_path=...`).
- **Periodic rotation** of the AppRole `secret_id`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/vault/integration-hashicorp/lab.yml
ansible-lint labs/vault/integration-hashicorp/challenge/solution.yml
ansible-lint --profile production labs/vault/integration-hashicorp/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task,
file modes as strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
