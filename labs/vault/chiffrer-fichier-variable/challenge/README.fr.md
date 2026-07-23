# 🎯 Challenge — Mixer variables chiffrées et claires sur `db1.lab`

## ✅ Objectif

Reproduire la mécanique d'`encrypt_string` du lab démo, mais cette fois
sur **`db1.lab`** avec un fichier produit **`/tmp/lab78-challenge.txt`**
contenant 3 lignes attendues.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/lab78-challenge.txt` |
| Variable `admin_username` | clair, valeur exacte `lab78_admin` |
| Variable `admin_password` | chiffrée via `encrypt_string`, doit commencer par `Admin…` |
| Le fichier doit afficher | `starts: Admin…`, `length: <N>` |

## 🧩 Bloqué ?

```bash
dsoxlab hint vault-chiffrer-fichier-variable
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

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

## 💡 Pour aller plus loin

- `ansible-vault encrypt_string --stdin-name admin_password` pour saisir
  la valeur via stdin (pas dans l'historique shell).
- Re-chiffrer la valeur sans changer de mot de passe : éditer le YAML et
  régénérer.
