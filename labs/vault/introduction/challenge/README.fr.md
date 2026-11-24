# Le mot de passe de la base est dans l'historique Git

## La situation

L'audit de sécurité l'a trouvé ce matin : un `db_secrets.yml` commité en clair il
y a dix-huit mois, toujours lisible par quiconque peut cloner le dépôt. Supprimer
le fichier ne change rien, Git se souvient. Le mot de passe tourne aujourd'hui, et
le nouveau n'ira pas s'écrire dans un YAML en clair. Ce que le dépôt contiendra
désormais, c'est du chiffré, déchiffré au dernier moment sur le nœud de contrôle.

Votre mission, depuis **control-node.lab** :

1. Chiffrer les deux fichiers de secrets dont l'application a besoin, pour que ce
   qui atterrit dans Git soit illisible sans le mot de passe vault, et vérifier
   que le chiffrement est réel en inspectant le fichier.
2. Consulter et modifier un fichier chiffré **sans** laisser traîner de copie
   déchiffrée sur le disque.
3. Faire consommer les **deux** fichiers chiffrés par un playbook en un seul run
   et prouver, sur **db1.lab**, que leurs valeurs sont arrivées intactes, dans un
   fichier lisible du seul root.
4. Traiter la rotation elle-même : changer le mot de passe vault d'un fichier
   existant, et savoir remettre un fichier en clair quand il n'a plus de secret.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/secrets-vault/ansible-vault-introduction/

## 🎯 Challenge — combiner 2 fichiers vault différents dans un seul play

Ce challenge utilise **deux fichiers chiffrés** (`db_secrets.yml` et
`api_secrets.yml`, déjà livrés dans `challenge/`) dans un seul playbook.
Les deux ont été chiffrés avec le **même mot de passe vault** :
**`lab77-vault-2026`**.

Ce mot de passe est **imposé**, pas choisi : les fichiers livrés ont été
chiffrés avec lui, c'est donc le seul qui les ouvre.

### ✅ Objectif

Sur **`db1.lab`**, déposer `/tmp/lab77-challenge-result.txt` (mode `0600`)
qui prouve que les **deux** fichiers chiffrés ont été déchiffrés.

| Marqueur attendu dans le fichier | Vient de |
| --- | --- |
| `db_user: app_admin` | `db_secrets.yml` |
| `api_endpoint: https://api.example.com/v1` | `api_secrets.yml` |
| `ChallengeDB2026` (préfixe du `db_password`) | `db_secrets.yml` |
| `challenge_api_xyz789` (l'`api_key`) | `api_secrets.yml` |

### 🧩 Squelette à compléter

Étape 1 : vérifier que le mot de passe vault du lab est en place. Le fichier
`.vault_password` est gitignoré (on ne commite jamais un mot de passe), il est
donc absent d'un clone frais. La commande suivante le pose pour vous :

```bash
scripts/setup-lab-vault-passwords.sh           # pose le .vault_password du lab
cat labs/vault/introduction/.vault_password    # → lab77-vault-2026
```

Si vous préférez le poser à la main :

```bash
cd labs/vault/introduction/
printf '%s' "lab77-vault-2026" > .vault_password
chmod 0600 .vault_password
```

Étape 2 : vérifier que vous ouvrez bien les fichiers livrés :

```bash
ansible-vault view \
    --vault-password-file labs/vault/introduction/.vault_password \
    labs/vault/introduction/challenge/db_secrets.yml
```

Étape 3 : écrire `challenge/solution.yml` :

```yaml
---
- name: Challenge 77 — combiner 2 fichiers chiffrés sur db1
  hosts: ???
  become: ???
  gather_facts: false
  vars_files:
    - ???                              # db_secrets.yml (chiffré)
    - ???                              # api_secrets.yml (chiffré)

  tasks:
    - name: Déposer le fichier-résultat avec preuve de déchiffrement
      ansible.builtin.copy:
        dest: ???                      # /tmp/lab77-challenge-result.txt
        content: |
          db_user: {{ ??? }}
          db_password: {{ ??? }}
          api_endpoint: {{ ??? }}
          api_key: {{ ??? }}
        mode: ???                      # 0600 (secrets)
      no_log: ???                      # niveau task — pas dans copy:
```

> 💡 **Pièges** :
>
> - **`vars_files:`** charge les fichiers chiffrés ET non chiffrés —
>   Ansible détecte le header `$ANSIBLE_VAULT` automatiquement.
> - **Chemins relatifs** : `vars_files: [db_secrets.yml]` cherche depuis
>   `playbook_dir`. Comme votre `solution.yml` est dans `challenge/`, le
>   chemin est juste `db_secrets.yml` (les 2 fichiers chiffrés sont
>   livrés dans le même dossier).
> - **`no_log: true`** est un keyword **task-level**, pas un paramètre du
>   module `copy:`. Le placer au niveau du module donne une erreur
>   `Unsupported parameters`.
> - **Mode `0600`** indispensable : un fichier qui contient un password
>   doit être lisible uniquement par root.

### 🚀 Lancement

```bash
ansible-playbook \
    --vault-password-file labs/vault/introduction/.vault_password \
    labs/vault/introduction/challenge/solution.yml
```

> Le `conftest.py` injecte automatiquement `--vault-password-file` lors
> du replay pytest — vous n'avez pas besoin de le repasser pour les
> tests automatisés.

### 🧪 Validation

```bash
pytest -v labs/vault/introduction/challenge/tests/
```

6 tests : fichier existant, `db_user`, `api_endpoint`, préfixe du
`db_password`, `api_key` présent, et **idempotence** (un second passage du
playbook doit afficher `changed=0` partout dans le `PLAY RECAP`, c'est le
critère RHCE).

### 🧹 Reset

```bash
dsoxlab clean vault-introduction
```

### 💡 Pour aller plus loin

- **`ansible-vault rekey`** : changer le mot de passe vault sans toucher
  au contenu (rotation périodique).
- **`--ask-vault-pass`** : saisie interactive plutôt que fichier.
- **Vérifier que les fichiers chiffrés sont commitable** : `grep
  app_admin db_secrets.yml` ne doit retourner **aucun** résultat.
