# 🎯 Challenge — Vault-id séparés `dev` et `prod`

## ✅ Objectif

Démontrer que **2 vault-id différents** (`dev` et `prod`) déchiffrent
correctement leurs **propres fichiers** sur leurs **propres hôtes**.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `web1.lab` (groupe `dev`) | `/tmp/lab79-challenge-web1.lab.txt` | `dev-db.example.com`, `Environnement: dev`, `length: 12` |
| `db1.lab` (groupe `prod`) | `/tmp/lab79-challenge-db1.lab.txt` | `prod-db.example.com`, `Environnement: prod`, `length: 26` |

## 🧩 Bloqué ?

```bash
dsoxlab hint vault-id-multiples
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

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

## 💡 Pour aller plus loin

- **3+ vault-id** (dev/staging/prod/secret) : Ansible essaie chaque
  vault-id en cascade jusqu'à trouver le bon.
- **`@prompt`** au lieu de fichier : `--vault-id prod@prompt` pour
  saisir interactivement.
- **`server_list:`** dans `ansible.cfg` pour multi-Galaxy + multi-vault.
