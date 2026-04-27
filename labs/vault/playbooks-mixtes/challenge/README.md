# 🎯 Challenge — Mixer `main.yml` (clair) + `vault.yml` (chiffré) par groupe

## ✅ Objectif

Démontrer le pattern production : un `group_vars/<grp>/main.yml` avec
**variables non sensibles en clair**, et un `group_vars/<grp>/vault.yml`
**chiffré** avec les mots de passe / tokens. Les deux fichiers sont
chargés automatiquement par Ansible au runtime.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `web1.lab` | `/tmp/lab80-challenge.txt` | `Env: lab80`, `Port: 80`, `Admin token starts: lab80_admi`, `Web secret length: 20` |

## 🧩 Indices

### Structure attendue

```text
group_vars/
├── all/
│   ├── main.yml           ← env_name, env_port (clair)
│   └── vault.yml          ← vault_admin_token (chiffré)
└── webservers/
    ├── main.yml           ← variables propres aux webservers (clair)
    └── vault.yml          ← vault_web_secret (chiffré)
```

### Étape 1 — Variables en clair

```yaml
# group_vars/all/main.yml
---
env_name: ???              # doit afficher "Env: lab80"
env_port: ???              # doit afficher "Port: 80"
```

### Étape 2 — Variables sensibles (chiffrées)

```bash
echo "vault-mixte-2026" > .vault_password && chmod 0600 .vault_password

cat > group_vars/all/vault.yml <<'YAML'
---
vault_admin_token: ???     # doit commencer par "lab80_admi" (chars 0-9)
YAML
ansible-vault encrypt group_vars/all/vault.yml --vault-password-file=.vault_password

cat > group_vars/webservers/vault.yml <<'YAML'
---
vault_web_secret: ???      # exactement 20 caractères
YAML
ansible-vault encrypt group_vars/webservers/vault.yml --vault-password-file=.vault_password
```

### Étape 3 — Écrire `challenge/solution.yml`

```yaml
---
- name: Challenge 80 — playbook mixte clair + vault sur webservers
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: Déposer le marqueur lab80
      ansible.builtin.copy:
        dest: ???
        content: |
          Env: {{ env_name }}
          Port: {{ env_port }}
          Admin token starts: {{ vault_admin_token[:10] }}
          Web secret length: {{ vault_web_secret | length }}
        mode: "0600"
      no_log: ???
```

> 💡 **Pièges** :
>
> - **Convention `vault_*`** : préfixer les variables sensibles. Permet
>   de **`grep -r vault_ inventory/`** pour auditer tous les secrets.
> - **`group_vars/<grp>/main.yml` + `vault.yml`** : Ansible charge les
>   2 fichiers et merge. Pas besoin de `vars_files:` explicite.
> - **Précédence** : `group_vars/<grp>/` > `group_vars/all/`. Donc une
>   variable dans `webservers/vault.yml` override `all/vault.yml`.
> - **Diff lisible** : seul `vault.yml` est chiffré. `main.yml` reste
>   en clair → diffs Git lisibles sur les vars non sensibles.

## 🚀 Lancement

```bash
ansible-playbook labs/vault/playbooks-mixtes/challenge/solution.yml \
    --vault-password-file=labs/vault/playbooks-mixtes/.vault_password
```

## 🧪 Validation

```bash
pytest -v labs/vault/playbooks-mixtes/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/vault/playbooks-mixtes/ clean
```

## 💡 Pour aller plus loin

- **Convention** : préfixer les variables vault par `vault_` pour
  documenter leur sensibilité.
- **Deux fichiers vs un fichier `!vault |` inline** : préférer la
  séparation sur des projets multi-équipe.
- **Précédence** : `group_vars/<grp>/*` > `group_vars/all/*` —
  `webservers` peut overrider une valeur de `all`.
