# 🎯 Challenge — Pattern `vault.yml` dans un rôle

## ✅ Objectif

Démontrer le pattern de production : un rôle `secured_app` avec
**`defaults/main.yml`** (variables non sensibles, surchargeables) et
**`vars/main.yml`** (variables vault, chiffrées). Le test valide qu'un
override par le play marche, et que les 2 secrets chiffrés sont
correctement déchiffrés à l'exécution.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `db1.lab` | `/tmp/lab81-secured-app.txt` | `user: appuser`, `port: 9999`, `RoleDBPas…` (9 premiers chars du db_password), `role_api_tok_lab81_xyz` |

## 🧩 Bloqué ?

```bash
dsoxlab hint vault-dans-roles
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

## 🚀 Lancement

```bash
ansible-playbook labs/vault/dans-roles/challenge/solution.yml \
    --vault-password-file=labs/vault/dans-roles/.vault_password \
    -e ansible_roles_path=labs/vault/dans-roles/roles
```

## 🧪 Validation

```bash
pytest -v labs/vault/dans-roles/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean vault-dans-roles
```

## 💡 Pour aller plus loin

- **Convention `vault_*` + alias** : `secured_app_db_password: "{{ vault_secured_app_db_password }}"` permet de chiffrer une seule fois et exposer une variable claire au reste du rôle.
- **`tags:` sur les rôles** pour skipper les tâches vault en mode `--check`.
- **Dépendances de rôle** : `meta/main.yml: dependencies` peut référencer
  un autre rôle qui charge le vault.
