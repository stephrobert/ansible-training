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

## 🧩 Indices

### Étape 1 — Préparer le mot de passe vault

```bash
cd labs/premiers-pas/ansible-vault/challenge/

echo "??? choisissez un mot de passe robuste ???" > .vault_password
chmod ??? .vault_password
```

### Étape 2 — Créer le fichier de secrets en clair

```bash
mkdir -p files
cat > files/app_secrets.yml <<'EOF'
---
app_db_password: ???
app_jwt_secret:  ???
app_redis_token: ???
EOF
```

### Étape 3 — Chiffrer le fichier

```bash
ansible-vault ??? files/app_secrets.yml --vault-password-file=.vault_password
```

Vérification :

```bash
head -3 files/app_secrets.yml      # → doit commencer par $ANSIBLE_VAULT;1.1;AES256
```

### Étape 4 — Écrire `solution.yml`

Squelette à compléter (les `???` sont à deviner) :

```yaml
---
- name: Challenge 04b — déposer config applicative chiffrée
  hosts: ???
  become: ???
  gather_facts: false
  vars_files:
    - ???                          # le fichier chiffré

  tasks:
    - name: Déposer /tmp/db1-app.conf avec les 3 secrets
      ansible.builtin.copy:
        dest: ???
        content: |
          # config app — secrets déchiffrés au runtime
          db_password={{ ??? }}
          jwt_secret={{ ??? }}
          redis_token={{ ??? }}
        owner: ???
        group: ???
        mode: ???
        no_log: ???
```

> 💡 **Pièges** :
>
> - **`no_log: true`** est un keyword **task-level**, pas un paramètre du
>   module `copy:`. Le placer dans le module donne `Unsupported parameters`.
> - **Mode `0600`** indispensable pour `.vault_password` ET pour le fichier
>   de secrets déposé. Sans ça, autres users du système peuvent voler le
>   contenu.
> - **`vars_files: [files/app_secrets.yml]`** : chemin relatif au playbook.
>   Avec `solution.yml` dans `challenge/`, le chemin est juste
>   `files/app_secrets.yml` (pas `challenge/files/...`).
> - **Le test scanne le `.vault_password`** pour vérifier mode 0600. Mode
>   0644 fait échouer le test, même si le déchiffrement marche.

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

## 🧹 Reset

```bash
make -C labs/premiers-pas/ansible-vault/ clean
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
