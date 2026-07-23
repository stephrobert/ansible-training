# 🎯 Challenge — Separate `dev` and `prod` vault-ids

## ✅ Objective

Demonstrate that **2 different vault-ids** (`dev` and `prod`) decrypt
correctly their **own files** on their **own hosts**.

| Target | Produced file | Expected content |
| --- | --- | --- |
| `web1.lab` (group `dev`) | `/tmp/lab79-challenge-web1.lab.txt` | `dev-db.example.com`, `Environnement: dev`, `length: 12` |
| `db1.lab` (group `prod`) | `/tmp/lab79-challenge-db1.lab.txt` | `prod-db.example.com`, `Environnement: prod`, `length: 26` |

## 🧩 Stuck?

```bash
dsoxlab hint vault-id-multiples
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

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
