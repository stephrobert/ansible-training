# 🎯 Challenge — HashiCorp Vault / OpenBao: KV v2 lookup, proven

## ✅ Objective

Write `challenge/solution.yml`: a playbook that retrieves **at runtime**
the two secrets created in the local Vault (`db_password` and `api_key`,
path `secret/lab82`) via the `community.hashi_vault.vault_kv2_get` lookup,
and that deposits the **derived proof** (the lengths, never the values)
into a local file.

The tests require a **running Vault**: they query its
API themselves to check that what your playbook wrote matches the secrets
actually stored. Without a server, they `skip` with the steps
to follow: nothing passes "empty".

## 🔧 Prerequisites (the lab infrastructure)

```bash
cd labs/vault/integration-hashicorp/
./setup-vault.sh                          # dev Vault on 127.0.0.1:8200 (podman required)
ansible-galaxy collection install community.hashi_vault
pipx inject ansible hvac                  # Python Vault client
```

The script creates the demo secrets in `secret/lab82` and displays the dev
token (`lab82-root`).

## 🧩 Expected contract

| Element | Expectation |
| --- | --- |
| Target | `localhost`, `connection: local`, without `become` |
| Address and token | read from the environment (`VAULT_ADDR`, `VAULT_TOKEN`), with `http://127.0.0.1:8200` and `lab82-root` as defaults |
| Lookup | `community.hashi_vault.vault_kv2_get`, path `lab82`, explicit `engine_mount_point` |
| Proof | `/tmp/lab82-vault-lookup.txt`, mode `0600`, containing exactly the two lines `db_password length: <n>` and `api_key length: <n>` |
| Forbidden | any cleartext secret value, in the YAML as in the proof file |

## 🧩 Skeleton

```yaml
---
- name: Récupérer les secrets depuis Vault et en déposer la preuve
  hosts: ???
  connection: ???
  gather_facts: false
  become: false                        # ansible.cfg l'active globalement : pas ici

  vars:
    ansible_ssh_private_key_file: null   # localhost n'a pas besoin de la clé SSH du lab
    vault_addr: "{{ lookup('env', 'VAULT_ADDR') | default('???', true) }}"
    vault_token: "{{ lookup('env', 'VAULT_TOKEN') | default('???', true) }}"
    secrets: "{{ lookup('community.hashi_vault.vault_kv2_get',
                        '???',
                        engine_mount_point='???',
                        url=vault_addr,
                        token=vault_token).secret }}"

  tasks:
    - name: Déposer la preuve (longueurs, jamais les valeurs)
      ansible.builtin.copy:
        dest: ???
        content: |
          db_password length: {{ ??? }}
          api_key length: {{ ??? }}
        mode: ???
```

> 💡 **Pitfalls**:
>
> - **Missing collection**: `couldn't resolve module/action
>   'community.hashi_vault.vault_kv2_get'` means that
>   `ansible-galaxy collection install community.hashi_vault` is missing.
> - **`.secret`**: the lookup returns a dictionary; the key/value
>   pairs of the KV v2 live under its `secret` key.
> - **`engine_mount_point`**: in dev mode the KV v2 is mounted on `secret/`.
>   Without the explicit mount point, the lookup searches in the wrong place.
> - **Mode `0600`**: the proof only contains lengths, but the
>   reflex remains: a file derived from a secret is never deposited as `0644`.
> - **Dev root token**: accepted here only because the server is
>   disposable. In production: AppRole or JWT/OIDC, never the root token.
> - **`ansible_ssh_private_key_file: null`**: the lab inventory defines
>   the SSH key via `inventory_dir`, which the implicit `localhost` cannot
>   resolve. Without this neutralization, the play crashes before its 1st task.

## 🚀 Launch

```bash
ansible-playbook labs/vault/integration-hashicorp/challenge/solution.yml
cat /tmp/lab82-vault-lookup.txt
```

## 🧪 Validation

```bash
pytest -v labs/vault/integration-hashicorp/challenge/tests/
```

The tests read the secrets **directly in Vault** (HTTP API) and
compare: exact lengths in the proof, no cleartext value either
in the proof or in your YAML, and idempotence on the second run.

## 🧹 Reset

```bash
podman stop vault-lab82
rm -f /tmp/lab82-vault-lookup.txt
```

## 💡 Going further

- **OpenBao**: `podman stop vault-lab82 && IMAGE=openbao/openbao:latest
  ./setup-vault.sh`, then run the playbook and tests again: nothing to change,
  the API is compatible.
- **AppRole**: replace the token with `auth_method='approle'` with
  `role_id`/`secret_id` (cf. the lab README, exercise 4).
- **`ansible-lint --profile production labs/vault/integration-hashicorp/challenge/solution.yml`**.
