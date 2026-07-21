# 🎯 Challenge — HashiCorp Vault / OpenBao : lookup KV v2, prouvée

## ✅ Objectif

Écrire `challenge/solution.yml` : un playbook qui récupère **au runtime**
les deux secrets posés dans le Vault local (`db_password` et `api_key`,
chemin `secret/lab82`) via la lookup `community.hashi_vault.vault_kv2_get`,
et qui en dépose la **preuve dérivée** (les longueurs, jamais les valeurs)
dans un fichier local.

Les tests exigent un **Vault qui tourne** : ils interrogent eux-mêmes son
API pour vérifier que ce que votre playbook a écrit correspond aux secrets
réellement stockés. Sans serveur, ils se mettent en `skip` avec la marche à
suivre : rien ne passe « à vide ».

## 🔧 Pré-requis (infrastructure du lab)

```bash
cd labs/vault/integration-hashicorp/
./setup-vault.sh                          # Vault dev sur 127.0.0.1:8200 (podman requis)
ansible-galaxy collection install community.hashi_vault
pipx inject ansible hvac                  # client Python Vault
```

Le script pose les secrets de démo dans `secret/lab82` et affiche le token
dev (`lab82-root`).

## 🧩 Contrat attendu

| Élément | Attente |
| --- | --- |
| Cible | `localhost`, `connection: local`, sans `become` |
| Adresse et token | lus depuis l'environnement (`VAULT_ADDR`, `VAULT_TOKEN`), avec `http://127.0.0.1:8200` et `lab82-root` en défauts |
| Lookup | `community.hashi_vault.vault_kv2_get`, chemin `lab82`, `engine_mount_point` explicite |
| Preuve | `/tmp/lab82-vault-lookup.txt`, mode `0600`, contenant exactement les deux lignes `db_password length: <n>` et `api_key length: <n>` |
| Interdit | toute valeur de secret en clair, dans le YAML comme dans le fichier preuve |

## 🧩 Squelette

```yaml
---
- name: Récupérer les secrets depuis Vault et en déposer la preuve
  hosts: ???
  connection: ???
  gather_facts: false
  become: false                        # ansible.cfg l'active globalement : pas ici

  vars:
    ansible_ssh_private_key_file: null   # localhost n'a pas besoin de la clé SSH du lab
    vault_addr: "{{ lookup('env', 'VAULT_ADDR') | default('???', true) }}"
    vault_token: "{{ lookup('env', 'VAULT_TOKEN') | default('???', true) }}"
    secrets: "{{ lookup('community.hashi_vault.vault_kv2_get',
                        '???',
                        engine_mount_point='???',
                        url=vault_addr,
                        token=vault_token).secret }}"

  tasks:
    - name: Déposer la preuve (longueurs, jamais les valeurs)
      ansible.builtin.copy:
        dest: ???
        content: |
          db_password length: {{ ??? }}
          api_key length: {{ ??? }}
        mode: ???
```

> 💡 **Pièges** :
>
> - **Collection absente** : `couldn't resolve module/action
>   'community.hashi_vault.vault_kv2_get'` signifie que
>   `ansible-galaxy collection install community.hashi_vault` manque.
> - **`.secret`** : la lookup retourne un dictionnaire ; les paires
>   clé/valeur du KV v2 vivent sous sa clé `secret`.
> - **`engine_mount_point`** : en dev mode le KV v2 est monté sur `secret/`.
>   Sans le point de montage explicite, la lookup cherche au mauvais endroit.
> - **Mode `0600`** : la preuve ne contient que des longueurs, mais le
>   réflexe reste : un fichier issu d'un secret ne se pose jamais en `0644`.
> - **Token root de dev** : accepté ici uniquement parce que le serveur est
>   jetable. En production : AppRole ou JWT/OIDC, jamais le token root.
> - **`ansible_ssh_private_key_file: null`** : l'inventaire du lab définit
>   la clé SSH via `inventory_dir`, que l'implicite `localhost` ne sait pas
>   résoudre. Sans cette neutralisation, le play plante avant sa 1ère tâche.

## 🚀 Lancement

```bash
ansible-playbook labs/vault/integration-hashicorp/challenge/solution.yml
cat /tmp/lab82-vault-lookup.txt
```

## 🧪 Validation

```bash
pytest -v labs/vault/integration-hashicorp/challenge/tests/
```

Les tests lisent les secrets **directement dans Vault** (API HTTP) et
comparent : longueurs exactes dans la preuve, aucune valeur en clair ni
dans la preuve ni dans votre YAML, et idempotence au second passage.

## 🧹 Reset

```bash
podman stop vault-lab82
rm -f /tmp/lab82-vault-lookup.txt
```

## 💡 Pour aller plus loin

- **OpenBao** : `podman stop vault-lab82 && IMAGE=openbao/openbao:latest
  ./setup-vault.sh`, puis relancez playbook et tests : rien à changer,
  l'API est compatible.
- **AppRole** : remplacez le token par `auth_method='approle'` avec
  `role_id`/`secret_id` (cf. README du lab, exercice 4).
- **`ansible-lint --profile production labs/vault/integration-hashicorp/challenge/solution.yml`**.
