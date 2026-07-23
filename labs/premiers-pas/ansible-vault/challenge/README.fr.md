# 🎯 Challenge — Configuration applicative chiffrée sur `db1.lab`

## ✅ Objectif

Déposer une configuration applicative chiffrée sur `db1.lab`, contenant
**3 secrets** différents.

| Élément | Valeur attendue |
| --- | --- |
| Hôte cible | `db1.lab` |
| Fichier produit | `/tmp/db1-app.conf` |
| Permissions | `0600`, owner `root` |
| Variable `app_db_password` | doit apparaître dans le fichier |
| Variable `app_jwt_secret` | doit apparaître dans le fichier |
| Variable `app_redis_token` | doit apparaître dans le fichier |
| Source des secrets | **fichier YAML chiffré** (`challenge/files/app_secrets.yml`) |
| Mot de passe vault | `challenge/.vault_password` (mode `0600`, gitignored) |

## 🧩 Bloqué ?

```bash
dsoxlab hint premiers-pas-ansible-vault
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

Depuis la racine du repo :

```bash
ansible-playbook labs/premiers-pas/ansible-vault/challenge/solution.yml \
    --vault-password-file=labs/premiers-pas/ansible-vault/challenge/.vault_password
```

## 🧪 Validation automatisée

```bash
pytest -v labs/premiers-pas/ansible-vault/challenge/tests/
```

Le test `pytest+testinfra` valide :

- `/tmp/db1-app.conf` existe sur `db1.lab` avec mode `0600` et owner `root`.
- Les 3 variables (`db_password=`, `jwt_secret=`, `redis_token=`) sont
  présentes dans le contenu.
- Le fichier `challenge/files/app_secrets.yml` est bien **chiffré**
  (commence par `$ANSIBLE_VAULT`).
- Le fichier `challenge/.vault_password` a bien `mode 0600`.
- La solution est **idempotente** : un second passage n'annonce aucun changement (critère RHCE).

## 🧹 Reset

```bash
dsoxlab clean premiers-pas-ansible-vault
```

## 💡 Pour aller plus loin

- **`ANSIBLE_VAULT_PASSWORD_FILE=…`** dans `.env` ou `~/.bashrc` du
  poste de travail pour ne plus taper `--vault-password-file`.
- **`ansible-vault rekey`** : changer le mot de passe vault sans
  toucher au contenu (rotation périodique).
- **Précédence des secrets** : `vars_files:` > `defaults/main.yml` —
  attention aux collisions.
- **`ansible-lint --profile production`** détecte les fichiers de
  secrets non chiffrés et le manque de `no_log:` sur les tâches
  sensibles.
