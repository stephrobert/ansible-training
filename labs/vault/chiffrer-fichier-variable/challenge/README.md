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

## 🧩 Indices

### Étape 1 — Définir les variables dans `host_vars/db1.lab.yml`

```bash
mkdir -p host_vars/
cat > host_vars/db1.lab.yml <<'YAML'
---
admin_username: ???                     # en CLAIR
admin_password: !vault |                # CHIFFRÉ inline
  $ANSIBLE_VAULT;1.1;AES256
  ???
YAML
```

### Étape 2 — Générer la valeur chiffrée

```bash
ansible-vault encrypt_string --vault-password-file=.vault_password \
    'AdminP@ss-2026!' --name admin_password
```

→ Copier la sortie dans `host_vars/db1.lab.yml`.

### Étape 3 — Écrire `challenge/solution.yml`

```yaml
---
- name: Challenge 78 — déposer marqueur sur db1.lab
  hosts: ???
  become: ???
  gather_facts: false
  tasks:
    - name: Vérifier que les variables chiffrée et claire sont déchiffrées
      ansible.builtin.copy:
        dest: ???
        content: |
          username: {{ admin_username }}
          starts: {{ admin_password[:5] }}…
          length: {{ admin_password | length }}
        mode: "0600"
      no_log: ???
```

> 💡 **Pièges** :
>
> - **`encrypt_string`** chiffre une **valeur**, pas un fichier complet.
>   Le tag `!vault |` Yaml indique à Ansible de la déchiffrer au runtime.
> - **`encrypt_string --stdin-name <var>`** pour saisir la valeur via
>   stdin (pas dans l'historique shell). Plus propre.
> - **Indentation du `!vault |`** : critique en YAML — la valeur chiffrée
>   doit être indentée sous le tag. Copier la sortie d'`ansible-vault
>   encrypt_string` telle quelle.
> - **`no_log: true`** au niveau task. Sans, `ansible-playbook -v` peut
>   afficher la valeur déchiffrée dans le résultat de la tâche.

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
make -C labs/vault/chiffrer-fichier-variable/ clean
```

## 💡 Pour aller plus loin

- `ansible-vault encrypt_string --stdin-name admin_password` pour saisir
  la valeur via stdin (pas dans l'historique shell).
- Re-chiffrer la valeur sans changer de mot de passe : éditer le YAML et
  régénérer.
