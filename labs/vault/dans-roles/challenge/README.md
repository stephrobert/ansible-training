# 🎯 Challenge — Pattern `vault.yml` dans un rôle

## ✅ Objectif

Démontrer le pattern de production : un rôle `secured_app` avec
**`defaults/main.yml`** (variables non sensibles, surchargeables) et
**`vars/main.yml`** (variables vault, chiffrées). Le test valide qu'un
override par le play marche, et que les 2 secrets chiffrés sont
correctement déchiffrés à l'exécution.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `db1.lab` | `/tmp/lab81-secured-app.txt` | `user: appuser`, `port: 9999`, `RoleDBPas…` (8 premiers chars du db_password), `role_api_tok_lab81_xyz` |

## 🧩 Indices

### Structure attendue du rôle

```text
roles/secured_app/
├── defaults/main.yml      ← secured_app_user, secured_app_port (clair, basse précédence)
├── vars/main.yml          ← vault_secured_app_db_password, vault_secured_app_api_token (chiffré)
└── tasks/main.yml         ← compose le marqueur final
```

### Étape 1 — Defaults (clair)

```yaml
# roles/secured_app/defaults/main.yml
---
secured_app_user: ???       # → "user: appuser"
secured_app_port: ???       # default à 8080, le play l'override à 9999
```

### Étape 2 — Vars (chiffré)

```bash
echo "vault-roles-2026" > .vault_password && chmod 0600 .vault_password

cat > roles/secured_app/vars/main.yml <<'YAML'
---
vault_secured_app_db_password: ???       # commence par "RoleDBPas" (9 chars)
vault_secured_app_api_token: ???          # exactement "role_api_tok_lab81_xyz"
secured_app_db_password: "{{ vault_secured_app_db_password }}"
secured_app_api_token: "{{ vault_secured_app_api_token }}"
YAML

ansible-vault encrypt roles/secured_app/vars/main.yml --vault-password-file=.vault_password
```

### Étape 3 — Tâche du rôle

```yaml
# roles/secured_app/tasks/main.yml
---
- name: Déposer le marqueur lab81
  ansible.builtin.copy:
    dest: /tmp/lab81-secured-app.txt
    content: |
      user: {{ secured_app_user }}
      port: {{ secured_app_port }}
      db_starts: {{ secured_app_db_password[:9] }}
      api_token: {{ secured_app_api_token }}
    mode: "0600"
  no_log: ???
```

### Étape 4 — `challenge/solution.yml`

```yaml
---
- name: Challenge 81 — invoquer le rôle secured_app sur db1
  hosts: ???
  become: ???
  gather_facts: false
  roles:
    - role: secured_app
      vars:
        secured_app_port: 9999       # override du default
```

> 💡 **Pièges** :
>
> - **`defaults/main.yml`** (priorité 1) vs **`vars/main.yml`** (priorité
>   18) : tout ce qui est dans `vars/` ne peut **pas** être overridé par
>   un `--extra-vars` du play. Les utilisateurs du rôle modifient les
>   `defaults/`, pas les `vars/`.
> - **Pattern d'indirection** : `vars/main.yml` chiffré contient
>   `vault_*`, puis `defaults/main.yml` clair fait
>   `app_var: "{{ vault_app_var }}"`. Le rôle utilise `app_var`,
>   l'utilisateur ne voit que les `defaults/`.
> - **`ANSIBLE_ROLES_PATH`** doit pointer sur le dossier parent du rôle.
>   Pas le rôle lui-même.
> - **Distribution du rôle** : ne jamais inclure le `.vault_password` dans
>   le tarball Galaxy. L'utilisateur fournit le sien via
>   `--vault-password-file`.

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
make -C labs/vault/dans-roles/ clean
```

## 💡 Pour aller plus loin

- **Convention `vault_*` + alias** : `secured_app_db_password: "{{ vault_secured_app_db_password }}"` permet de chiffrer une seule fois et exposer une variable claire au reste du rôle.
- **`tags:` sur les rôles** pour skipper les tâches vault en mode `--check`.
- **Dépendances de rôle** : `meta/main.yml: dependencies` peut référencer
  un autre rôle qui charge le vault.
