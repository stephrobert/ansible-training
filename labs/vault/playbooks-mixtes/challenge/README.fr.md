# 🎯 Challenge — Mixer `main.yml` (clair) + `vault.yml` (chiffré) par groupe

## ✅ Objectif

Démontrer le pattern production : un `group_vars/<grp>/main.yml` avec
**variables non sensibles en clair**, et un `group_vars/<grp>/vault.yml`
**chiffré** avec les mots de passe / tokens. Les deux fichiers sont
chargés automatiquement par Ansible au runtime.

| Cible | Fichier produit | Contenu attendu |
| --- | --- | --- |
| `web1.lab` | `/tmp/lab80-challenge.txt` | `Env: lab80`, `Port: 80`, `Admin token starts: lab80_admi`, `Web secret length: 20` |

## 🧩 Bloqué ?

```bash
dsoxlab hint vault-playbooks-mixtes
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

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
dsoxlab clean vault-playbooks-mixtes
```

## 💡 Pour aller plus loin

- **Convention** : préfixer les variables vault par `vault_` pour
  documenter leur sensibilité.
- **Deux fichiers vs un fichier `!vault |` inline** : préférer la
  séparation sur des projets multi-équipe.
- **Précédence** : `group_vars/<grp>/*` > `group_vars/all/*` —
  `webservers` peut overrider une valeur de `all`.
