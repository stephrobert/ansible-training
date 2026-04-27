# 🎯 Challenge — HashiCorp Vault / OpenBao : lookup KV v2

## ✅ Objectif

Vérifier que le projet contient un script de setup d'un Vault local
(HashiCorp ou OpenBao) **et** un playbook qui consomme les secrets via
la lookup `community.hashi_vault.vault_kv2_get` — **sans** jamais
écrire les secrets en clair dans le YAML.

| Fichier | Attente |
| --- | --- |
| `setup-vault.sh` | Exécutable. Variable `IMAGE` (toggle Vault ↔ OpenBao). Référence `hashicorp/vault` ou `openbao/openbao`. |
| `playbook.yml` | Utilise `community.hashi_vault.vault_kv2_get` via `lookup()`. `engine_mount_point` explicite (`secret`). Pas de valeur secrète en dur. |

## 🧩 Indices

### Étape 1 — Démarrer le Vault local

```bash
cd labs/vault/integration-hashicorp/
./setup-vault.sh                # → container Vault dev sur 127.0.0.1:8200
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root           # token dev (NE PAS UTILISER EN PROD)
```

### Étape 2 — Stocker un secret dans le KV v2

```bash
vault kv put secret/lab82 db_password=??? api_token=???
vault kv get secret/lab82
```

### Étape 3 — Compléter `playbook.yml`

Squelette à remplir :

```yaml
---
- name: Lab 82 — récupérer secret depuis HashiCorp Vault
  hosts: localhost
  gather_facts: false
  collections:
    - community.hashi_vault         # ← obligatoire

  vars:
    secrets: "{{ lookup('community.hashi_vault.vault_kv2_get',
                         '???',                          # path : 'lab82'
                         engine_mount_point='???',       # 'secret'
                         url='{{ lookup(\"env\", \"VAULT_ADDR\") }}',
                         token='{{ lookup(\"env\", \"VAULT_TOKEN\") }}') }}"

  tasks:
    - name: Afficher la longueur du db_password (preuve de récupération)
      ansible.builtin.debug:
        msg: "DB password length: {{ secrets.data.db_password | length }}"
      no_log: ???
```

## 🚀 Lancement

```bash
cd labs/vault/integration-hashicorp/
./setup-vault.sh
ansible-playbook playbook.yml
```

## 🧪 Validation

Le test pytest est **structurel** (fichiers + leur contenu, pas
l'exécution). Il marche **sans** lancer le container :

```bash
pytest -v labs/vault/integration-hashicorp/challenge/tests/
```

## 🧹 Reset

```bash
make -C labs/vault/integration-hashicorp/ clean
```

> 💡 **Pièges** :
>
> - **Collection requise** : `ansible-galaxy collection install
>   community.hashi_vault` est nécessaire avant le run. Erreur
>   `couldn't resolve module/action 'community.hashi_vault.vault_kv2_get'`
>   = collection absente.
> - **Token `root` en dev mode uniquement** : Vault dev mode démarre avec
>   `VAULT_TOKEN=root` et les données en mémoire (perdues au stop).
>   **JAMAIS** en prod. Pour la prod, utiliser `approle` ou `JWT/OIDC`.
> - **`engine_mount_point`** : par défaut le KV v2 est monté sur
>   `secret/` en dev mode (`engine_mount_point: secret`). En prod, c'est
>   souvent `kv/` ou un nom custom.
> - **Pas de valeur en dur** dans le playbook : le test pytest **scanne**
>   le fichier pour des chaînes interdites (`VaultPassLab82`,
>   `vault_api_xyz_lab82`). Utilisez la lookup, pas une valeur.
> - **`no_log: true`** sur les tâches qui manipulent le secret — sinon
>   `ansible-playbook -v` affiche tout.

## 💡 Pour aller plus loin

- **`approle`** auth method (au lieu de `token`) pour CI/CD : token
  long-vivant remplacé par role_id + secret_id à courte durée.
- **TLS** : Vault prod en HTTPS avec certificat client.
- **AppRole + Vault Agent** : sidecar qui injecte les secrets dans
  l'environnement sans qu'Ansible ait à les chercher.
