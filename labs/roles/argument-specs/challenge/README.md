# 🎯 Challenge — Argument specs avec valeurs valides + invalides

## ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** utilise le rôle
`webserver` avec des **valeurs valides** pour démontrer que :

1. Le rôle s'exécute sans erreur sur des valeurs valides.
2. Le test pytest peut **lancer la même solution avec une valeur invalide
   passée en `--extra-vars`** et observer qu'`argument_specs` la rejette.

## 🧩 Indices

Le rôle a `argument_specs.yml` qui contient en particulier :

```yaml
webserver_state:
  type: str
  default: present
  choices: [present, absent, latest]

webserver_service_state:
  type: str
  default: started
  choices: [started, stopped, restarted, reloaded]

webserver_listen_port:
  type: int
  default: 80
```

## 🧩 Squelette

```yaml
---
# Challenge — démontrer que argument_specs valide automatiquement les entrées.
- name: Challenge - webserver avec argument_specs
  hosts: ???
  become: ???

  roles:
    - role: webserver
      vars:
        webserver_listen_port: ???       # Le test attend 8090
        webserver_state: ???             # ← choix VALIDE parmi present/absent/latest
        webserver_service_state: ???     # ← choix VALIDE parmi started/stopped/restarted/reloaded
        webserver_index_content: "Lab 61 argument_specs validés sur {{ inventory_hostname }}"
```

> 💡 **Pièges** :
>
> - **Validation au runtime** : `argument_specs.yml` génère une tâche
>   automatique `Validating arguments against arg spec 'main'` au tout
>   début du rôle. Si une valeur est invalide, le play **plante avant
>   d'exécuter la moindre tâche**.
> - **`type: int` strict** : si vous passez `webserver_listen_port: "8090"`
>   (string entre guillemets), Ansible 2.18+ peut accepter et caster, mais
>   **certaines configurations strictes** rejettent. Préférez sans
>   guillemets pour les nombres.
> - **`choices:` insensible à la casse** : non, c'est sensible. `Started`
>   ≠ `started` — respect strict de la valeur déclarée dans `choices:`.
> - **Test avec `--extra-vars`** : le conftest n'a pas d'entrée
>   `_EXTRA_ARGS` pour ce lab — les `--extra-vars` du test pour
>   `valeur_invalide` sont passés via le test pytest lui-même
>   (subprocess).

## 🚀 Lancement

### Run normal (valeurs valides)

```bash
ansible-playbook labs/roles/argument-specs/challenge/solution.yml
```

🔍 Le rôle tourne normalement, vous voyez la tâche
`Validating arguments against arg spec 'main'` qui passe `ok`.

### Run avec valeur INVALIDE (à la main, pour observer le message)

```bash
ansible-playbook labs/roles/argument-specs/challenge/solution.yml \
    --extra-vars "webserver_state=valeur_invalide"
```

🔍 Sortie attendue :

```text
fatal: [db1.lab]: FAILED!
"argument_errors": [
  "value of webserver_state must be one of: present, absent, latest, got: valeur_invalide"
]
```

C'est exactement ce que le test pytest reproduit pour valider qu'argument_specs
est bien actif.

## 🧪 Validation automatisée

```bash
pytest -v labs/roles/argument-specs/challenge/tests/
```

Le test vérifie :

- `nginx` installé sur db1.
- `nginx.conf` contient `listen 8090` (preuve override de
  `webserver_listen_port`).
- Page d'accueil contient `argument_specs validés`.
- `meta/argument_specs.yml` existe et contient `argument_specs:` + `main:`.
- **Le test relance le playbook avec `webserver_state=valeur_invalide`** et
  vérifie qu'argument_specs rejette : exit non-zéro + message contenant
  `must be one of`.

## 🧹 Reset

```bash
make -C labs/roles/argument-specs clean
```

## 💡 Pour aller plus loin

- **Documenter une option `path:`** : pour des chemins vers fichiers.
  `argument_specs` ne vérifie pas l'existence — combinez avec `assert:`
  dans la 1ère tâche.
- **`type: dict` avec `options:` imbriquées** : valide la structure interne
  d'un dict. Très puissant pour des configs complexes.
- **Lint** :

  ```bash
  ansible-lint --profile production labs/roles/argument-specs/
  ```
