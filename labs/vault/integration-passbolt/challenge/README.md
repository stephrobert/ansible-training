# 🎯 Challenge — Passbolt: retrieve a secret, and prove it

## ✅ Objective

Write `challenge/solution.yml`: a playbook that authenticates against
your local Passbolt with **your OpenPGP key**, retrieves the secret
**`lab83-demo`** via the `anatomicjc.passbolt` collection, and deposits a
**derived** proof (the length of the password, never its value) into a
local file.

⚠️ **This lab has an irreducible manual part.** Passbolt authenticates
humans by OpenPGP key: the creation of the admin account, the generation of the
key and the creation of the secret go through the web interface. The tests
know it: as long as the server does not respond, the key is not exported
or the passphrase is not in the environment, they go into a
**`skip` with the steps to follow**. They never pass "empty".

## 🔧 Prerequisites (the manual steps, once)

```bash
cd labs/vault/integration-passbolt/
./setup-passbolt.sh                 # Passbolt CE + MariaDB (podman required)
```

Then, via the interface (`https://localhost:8443`, self-signed certificate):

1. Finish the admin registration with the link displayed by `register_user`.
2. Generate the account's OpenPGP key during the registration.
3. Create a resource named **`lab83-demo`** with a password.
4. Export the account's private key into
   `labs/vault/integration-passbolt/.passbolt-private.asc` (mode `0600`,
   the file is ignored by Git).

Finally, on the shell side:

```bash
ansible-galaxy collection install anatomicjc.passbolt
pipx inject ansible py-passbolt
export PASSBOLT_PASSPHRASE='<votre passphrase>'
```

## 🧩 Expected contract

| Element | Expectation |
| --- | --- |
| Target | `localhost`, `gather_facts: false`, without `become` |
| URL | env `PASSBOLT_URL`, default `https://localhost:8443`, `verify_ssl` disabled (dev, self-signed) |
| Private key | read from the lab's `.passbolt-private.asc` (lookup `file`) |
| Passphrase | env `PASSBOLT_PASSPHRASE`, never in the YAML |
| Secret | resource `lab83-demo`, via the lookup `anatomicjc.passbolt.passbolt` |
| Proof | `/tmp/lab83-passbolt-lookup.txt`, mode `0600`, content `Secret length: <n>` |
| Silence | `no_log: true` on any task that manipulates the secret |

## 🧩 Skeleton

```yaml
---
- name: Récupérer un secret Passbolt et en déposer la preuve
  hosts: ???
  gather_facts: false
  become: false                        # ansible.cfg l'active globalement : pas ici

  vars:
    ansible_ssh_private_key_file: null   # localhost n'a pas besoin de la clé SSH du lab
    passbolt_uri: "{{ lookup('env', 'PASSBOLT_URL') | default('???', true) }}"
    passbolt_private_key: "{{ lookup('file', '???') }}"
    passbolt_passphrase: "{{ lookup('env', '???') }}"

  tasks:
    - name: Récupérer le secret lab83-demo
      ansible.builtin.set_fact:
        demo_secret: "{{ lookup('anatomicjc.passbolt.passbolt',
                                '???',
                                uri=passbolt_uri,
                                private_key=passbolt_private_key,
                                passphrase=passbolt_passphrase,
                                verify_ssl=false).password }}"
      no_log: ???

    - name: Déposer la preuve (longueur, jamais la valeur)
      ansible.builtin.copy:
        dest: ???
        content: "Secret length: {{ ??? }}\n"
        mode: ???
```

> 💡 **Pitfalls**:
>
> - **The private key is a file, not a hardcoded variable**: a YAML that
>   embeds a PGP block is a YAML that ends up in Git.
> - **`no_log: true`** on the `set_fact`: without it, `-v` displays the secret.
> - **Path of the key**: `solution.yml` is played from the repo root
>   by pytest; use a path relative to `playbook_dir` or an absolute one.
> - **`verify_ssl=false`** only because the dev certificate is
>   self-signed. In production, never.
> - **`ansible_ssh_private_key_file: null`**: the lab inventory defines
>   the SSH key via `inventory_dir`, which the implicit `localhost` cannot
>   resolve. Without this neutralization, the play crashes before its 1st task.

## 🚀 Launch

```bash
export PASSBOLT_PASSPHRASE='<votre passphrase>'
ansible-playbook labs/vault/integration-passbolt/challenge/solution.yml
cat /tmp/lab83-passbolt-lookup.txt
```

## 🧪 Validation

```bash
pytest -v labs/vault/integration-passbolt/challenge/tests/
```

Reachable server + key + passphrase present: the tests replay your
playbook and check the proof on the system (existence, mode `0600`,
consistent length, no cleartext secret in the YAML). Otherwise: an explicit
`skip`, never a false green.

## 🧹 Reset

```bash
podman stop passbolt-app-lab83 passbolt-db-lab83
rm -f /tmp/lab83-passbolt-lookup.txt
```

## 💡 Going further

- **Passbolt vs HashiCorp Vault**: Passbolt targets the **human teams**
  (rich UI, sharing per group), Vault targets the **runtime** (dynamic
  secrets for services). Many organizations use both.
- **Bot account**: to automate without MFA, create a dedicated account with its
  own key and minimal rights.
- **Backup of the OpenPGP key**: without it, your secrets are lost.
