# La faute de frappe qui n'a explosé qu'au bout de dix minutes

## La situation

Hier, un collègue a appelé votre rôle `webserver` avec `webserver_state:
enabled`. Ce choix n'existe pas. Ansible n'a rien dit, a tourné dix minutes, puis
est mort au fond d'une tâche de paquet dans une trace illisible. La valeur était
fausse dès la première seconde, mais le rôle n'avait aucun moyen de le signaler.
Un rôle qui fait confiance à ses entrées fait payer son silence à ses
utilisateurs.

Votre mission, depuis **control-node.lab** :

1. Déployer le rôle `webserver` sur **db1.lab** avec des entrées **valides** :
   port d'écoute **8090**, un état de paquet et un état de service pris parmi les
   valeurs autorisées, et une page d'accueil personnalisée.
2. Faire en sorte que le rôle **type, contraigne et documente** ses variables
   d'entrée, pour qu'une valeur fausse soit rejetée **avant la première tâche**.
3. Lui passer volontairement une valeur invalide et lire le message de rejet :
   il doit nommer la variable et énumérer ce qui était permis.
4. Vérifier qu'un run aux valeurs valides franchit la validation sans accroc.

La méthode complète est dans le guide compagnon :
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/argument-specs/

## 🎯 Challenge — Argument specs avec valeurs valides + invalides

### ✅ Objectif

Écrire `challenge/solution.yml` qui sur **db1.lab** utilise le rôle
`webserver` avec des **valeurs valides** pour démontrer que :

1. Le rôle s'exécute sans erreur sur des valeurs valides.
2. Le test pytest peut **lancer la même solution avec une valeur invalide
   passée en `--extra-vars`** et observer qu'`argument_specs` la rejette.

### 🧩 Bloqué ?

```bash
dsoxlab hint roles-argument-specs
```

Les indices sont progressifs et **coûtent des points** : le premier oriente, le
dernier débloque.

### 🧩 Squelette

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

### 🚀 Lancement

#### Run normal (valeurs valides)

```bash
ansible-playbook labs/roles/argument-specs/challenge/solution.yml
```

🔍 Le rôle tourne normalement, vous voyez la tâche
`Validating arguments against arg spec 'main'` qui passe `ok`.

#### Run avec valeur INVALIDE (à la main, pour observer le message)

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

### 🧪 Validation automatisée

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

### 🧹 Reset

```bash
dsoxlab clean roles-argument-specs
```

### 💡 Pour aller plus loin

- **Documenter une option `path:`** : pour des chemins vers fichiers.
  `argument_specs` ne vérifie pas l'existence — combinez avec `assert:`
  dans la 1ère tâche.
- **`type: dict` avec `options:` imbriquées** : valide la structure interne
  d'un dict. Très puissant pour des configs complexes.
- **Lint** :

  ```bash
  ansible-lint --profile production labs/roles/argument-specs/
  ```
