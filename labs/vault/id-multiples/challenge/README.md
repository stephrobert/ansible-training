# 🎯 Challenge — Separate `dev` and `prod` vault-ids

## ✅ Objective

Demonstrate that **2 different vault-ids** (`dev` and `prod`) decrypt
correctly their **own files** on their **own hosts**.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `web1.lab` (group `dev`) | `/tmp/lab79-challenge-web1.lab.txt` | `dev-db.example.com`, `Environnement: dev`, `length: 12` |
| `db1.lab` (group `prod`) | `/tmp/lab79-challenge-db1.lab.txt` | `prod-db.example.com`, `Environnement: prod`, `length: 26` |

## 🧩 Hints

### Step 1 — Prepare 2 distinct vault passwords

```bash
echo "vault-dev-2026" > .vault_password_dev && chmod 0600 .vault_password_dev
echo "vault-prod-2026" > .vault_password_prod && chmod 0600 .vault_password_prod
```

### Step 2 — Encrypt 2 files with different vault-ids

```bash
mkdir -p group_vars/dev group_vars/prod

cat > group_vars/dev/vault.yml <<'YAML'
---
db_host: dev-db.example.com
db_password: ???       # à chiffrer avec vault-id dev
YAML

ansible-vault encrypt --vault-id dev@.vault_password_dev group_vars/dev/vault.yml

# Idem pour prod : DB host = prod-db.example.com, password 26 caractères
???
ansible-vault encrypt --vault-id prod@.vault_password_prod group_vars/prod/vault.yml
```

### Step 3 — Write `challenge/solution.yml`

```yaml
---
- name: Challenge 79 — déchiffrer dev (web1) et prod (db1) en parallèle
  hosts: ???      # tous les hôtes des 2 groupes
  become: ???
  gather_facts: false
  tasks:
    - name: Déposer le marqueur par hôte
      ansible.builtin.copy:
        dest: "/tmp/lab79-challenge-{{ inventory_hostname }}.txt"
        content: |
          Environnement: {{ env_name }}
          db_host: {{ db_host }}
          length: {{ db_password | length }}
        mode: "0600"
      no_log: ???
```

> 💡 **Pitfalls**:
>
> - **Format `--vault-id <label>@<source>`**: `<source>` can be a
>   file (`.vault_password_dev`), a script (executable `vault-pass.sh`),
>   or `prompt` (interactive input).
> - **Decryption cascade**: Ansible tries each vault-id
>   until it finds the right one. No fixed label → try order = CLI order.
> - **Header `$ANSIBLE_VAULT;1.2;AES256;<label>`**: the label is written
>   in the file. If you change the label, you must `rekey`.
> - **Security**: a `dev` vault-id CANNOT decrypt a file
>   encrypted with `prod`. This is the cryptographic guarantee of
>   environment separation.

## 🚀 Launch

```bash
ansible-playbook labs/vault/id-multiples/challenge/solution.yml \
    --vault-id dev@labs/vault/id-multiples/.vault_password_dev \
    --vault-id prod@labs/vault/id-multiples/.vault_password_prod \
    -i labs/vault/id-multiples/inventory/hosts.yml
```

## 🧪 Validation

```bash
pytest -v labs/vault/id-multiples/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean vault-id-multiples
```

## 💡 Going further

- **3+ vault-ids** (dev/staging/prod/secret): Ansible tries each
  vault-id in cascade until it finds the right one.
- **`@prompt`** instead of a file: `--vault-id prod@prompt` to
  enter it interactively.
- **`server_list:`** in `ansible.cfg` for multi-Galaxy + multi-vault.
