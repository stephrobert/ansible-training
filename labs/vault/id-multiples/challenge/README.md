# 🎯 Challenge — Vault-id séparés `dev` et `prod`

## ✅ Objectif

Démontrer que **2 vault-id différents** (`dev` et `prod`) déchiffrent
correctement leurs **propres fichiers** sur leurs **propres hôtes**.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `web1.lab` (groupe `dev`) | `/tmp/lab79-challenge-web1.lab.txt` | `dev-db.example.com`, `Environnement: dev`, `length: 12` |
| `db1.lab` (groupe `prod`) | `/tmp/lab79-challenge-db1.lab.txt` | `prod-db.example.com`, `Environnement: prod`, `length: 26` |

## 🧩 Indices

### Étape 1 — Préparer 2 mots de passe vault distincts

```bash
echo "vault-dev-2026" > .vault_password_dev && chmod 0600 .vault_password_dev
echo "vault-prod-2026" > .vault_password_prod && chmod 0600 .vault_password_prod
```

### Étape 2 — Chiffrer 2 fichiers avec vault-id différents

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

### Étape 3 — Écrire `challenge/solution.yml`

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

> 💡 **Pièges** :
>
> - **Format `--vault-id <label>@<source>`** : `<source>` peut être un
>   fichier (`.vault_password_dev`), un script (`vault-pass.sh` exécutable),
>   ou `prompt` (saisie interactive).
> - **Cascade de déchiffrement** : Ansible essaie chaque vault-id
>   jusqu'à trouver le bon. Pas de label fixe → ordre essai = ordre CLI.
> - **Header `$ANSIBLE_VAULT;1.2;AES256;<label>`** : le label est inscrit
>   dans le fichier. Si vous changez le label, vous devez `rekey`.
> - **Sécurité** : un vault-id `dev` ne peut PAS déchiffrer un fichier
>   chiffré avec `prod`. C'est la garantie cryptographique de la
>   séparation d'environnements.

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
make -C labs/vault/id-multiples/ clean
```

## 💡 Pour aller plus loin

- **3+ vault-id** (dev/staging/prod/secret) : Ansible essaie chaque
  vault-id en cascade jusqu'à trouver le bon.
- **`@prompt`** au lieu de fichier : `--vault-id prod@prompt` pour
  saisir interactivement.
- **`server_list:`** dans `ansible.cfg` pour multi-Galaxy + multi-vault.
