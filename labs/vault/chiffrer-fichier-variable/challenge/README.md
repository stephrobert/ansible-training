# 🎯 Challenge — Mix encrypted and cleartext variables on `db1.lab`

## ✅ Objective

Reproduce the `encrypt_string` mechanics of the demo lab, but this time
on **`db1.lab`** with a produced file **`/tmp/lab78-challenge.txt`**
containing 3 expected lines.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab78-challenge.txt` |
| Variable `admin_username` | cleartext, exact value `lab78_admin` |
| Variable `admin_password` | encrypted via `encrypt_string`, must start with `Admin…` |
| The file must display | `starts: Admin…`, `length: <N>` |

## 🧩 Hints

### Step 1 — Define the variables in `host_vars/db1.lab.yml`

```bash
mkdir -p host_vars/
cat > host_vars/db1.lab.yml <<'YAML'
---
admin_username: ???                     # en CLAIR
admin_password: !vault |                # CHIFFRÉ inline
  $ANSIBLE_VAULT;1.1;AES256
  ???
YAML
```

### Step 2 — Generate the encrypted value

```bash
ansible-vault encrypt_string --vault-password-file=.vault_password \
    'AdminP@ss-2026!' --name admin_password
```

→ Copy the output into `host_vars/db1.lab.yml`.

### Step 3 — Write `challenge/solution.yml`

```yaml
---
- name: Challenge 78 — déposer marqueur sur db1.lab
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: Vérifier que les variables chiffrée et claire sont déchiffrées
      ansible.builtin.copy:
        dest: ???
        content: |
          username: {{ admin_username }}
          starts: {{ admin_password[:5] }}…
          length: {{ admin_password | length }}
        mode: "0600"
      no_log: ???
```

> 💡 **Pitfalls**:
>
> - **`encrypt_string`** encrypts a **value**, not a complete file.
>   The `!vault |` YAML tag tells Ansible to decrypt it at runtime.
> - **`encrypt_string --stdin-name <var>`** to enter the value via
>   stdin (not in the shell history). Cleaner.
> - **Indentation of `!vault |`**: critical in YAML, the encrypted value
>   must be indented under the tag. Copy the output of `ansible-vault
>   encrypt_string` as is.
> - **`no_log: true`** at the task level. Without it, `ansible-playbook -v` may
>   display the decrypted value in the task result.

## 🚀 Launch

```bash
ansible-playbook labs/vault/chiffrer-fichier-variable/challenge/solution.yml \
    --vault-password-file=labs/vault/chiffrer-fichier-variable/.vault_password
```

## 🧪 Validation

```bash
pytest -v labs/vault/chiffrer-fichier-variable/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean vault-chiffrer-fichier-variable
```

## 💡 Going further

- `ansible-vault encrypt_string --stdin-name admin_password` to enter
  the value via stdin (not in the shell history).
- Re-encrypt the value without changing the password: edit the YAML and
  regenerate.
