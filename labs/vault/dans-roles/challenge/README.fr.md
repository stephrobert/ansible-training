# Le rôle embarque ses secrets, et personne ne peut les changer

## La situation

Le rôle `secured_app` voyage avec les identifiants dont il a besoin, chiffrés à
l'intérieur du rôle. Cela règle la distribution et crée un autre problème : une
équipe qui veut son propre mot de passe de base doit déchiffrer les entrailles du
rôle, les éditer, puis les rechiffrer. Alors elle forke. Trois forks plus tard, un
correctif de sécurité doit être appliqué quatre fois. Les secrets du rôle le
regardent ; les valeurs qu'un appelant utilise, non.

Votre mission, depuis **control-node.lab** :

1. Garder les secrets du rôle **chiffrés dans le rôle**, dans le fichier de
   variables que l'appelant n'est pas censé toucher.
2. Les exposer via des **variables publiques surchargeables** qui pointent vers
   les variables chiffrées : l'appelant voit un réglage, jamais du chiffré.
3. Prouver sur **db1.lab** que l'indirection fonctionne dans les deux sens : une
   valeur par défaut intacte résout bien le secret déchiffré, et une valeur
   surchargée depuis le play l'emporte.
4. Expliquer la précédence sur laquelle vous venez de vous appuyer, et pourquoi la
   variable publique devait vivre là où elle est pour que la surcharge soit
   seulement possible.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/vault-dans-roles/

## 🎯 Challenge — Pattern `vault.yml` dans un rôle

### ✅ Objectif

Démontrer le pattern de production : un rôle `secured_app` avec
**`defaults/main.yml`** (variables non sensibles, surchargeables) et
**`vars/main.yml`** (variables vault, chiffrées). Le test valide qu'un
override par le play marche, et que les 2 secrets chiffrés sont
correctement déchiffrés à l'exécution.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `db1.lab` | `/tmp/lab81-secured-app.txt` | `user: appuser`, `port: 9999`, `RoleDBPas…` (9 premiers chars du db_password), `role_api_tok_lab81_xyz` |

### 🧩 Bloqué ?

```bash
dsoxlab hint vault-dans-roles
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🚀 Lancement

```bash
ansible-playbook labs/vault/dans-roles/challenge/solution.yml \
    --vault-password-file=labs/vault/dans-roles/.vault_password \
    -e ansible_roles_path=labs/vault/dans-roles/roles
```

### 🧪 Validation

```bash
pytest -v labs/vault/dans-roles/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean vault-dans-roles
```

### 💡 Pour aller plus loin

- **Convention `vault_*` + alias** : `secured_app_db_password: "{{ vault_secured_app_db_password }}"` permet de chiffrer une seule fois et exposer une variable claire au reste du rôle.
- **`tags:` sur les rôles** pour skipper les tâches vault en mode `--check`.
- **Dépendances de rôle** : `meta/main.yml: dependencies` peut référencer
  un autre rôle qui charge le vault.
