# Lab 61 — Rôles : `argument_specs` (validation automatique)

> 💡 **Vous arrivez directement à ce lab sans avoir fait les précédents ?**
> Chaque lab de ce dépôt est **autonome**. Pré-requis unique : les 4 VMs du
> lab doivent répondre au ping Ansible.
>
> ```bash
> cd /home/bob/Projets/ansible-training
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```
>
> Si KO, lancez `make bootstrap && make provision` à la racine du repo (cf.
> [README racine](../../README.md#-démarrage-rapide) pour les détails).

## 🧠 Rappel

🔗 [**Argument specs Ansible : valider les entrées d'un rôle**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-roles/argument-specs/)

Sans `argument_specs`, **Ansible ne valide pas** les variables d'entrée d'un
rôle. Si l'utilisateur passe `webserver_listen_port: "abcd"` (string au lieu
d'int) ou `webserver_state: enabled` (au lieu de `present`), Ansible
exécute le rôle et **échoue tard** dans une tâche obscure.

**`argument_specs`** (depuis Ansible 2.11) **valide les entrées avant
l'exécution** : type, choix autorisés, valeurs requises. L'erreur est
**claire et précoce**.

| Sans argument_specs | Avec argument_specs |
| --- | --- |
| Erreur tardive dans une tâche obscure | Erreur **avant** la 1ère tâche |
| Stack trace Ansible interne | Message clair : *« must be one of: present, absent »* |
| Type silencieusement converti (int → str) | Échec si type incorrect |
| Variable manquante = valeur vide silencieuse | Échec explicite si `required: true` |

C'est le **standard de qualité** d'un rôle Galaxy moderne. `ansible-lint
--profile production` exige `meta/argument_specs.yml` pour les rôles publiés.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. Écrire un fichier `meta/argument_specs.yml` qui documente toutes les
   variables d'un rôle.
2. Définir le **type** d'une variable (`str`, `int`, `bool`, `list`, `dict`).
3. Restreindre les valeurs avec **`choices:`** (énumération).
4. Marquer une variable **`required: true`**.
5. Fournir une **valeur `default`** documentée.
6. Voir le **message d'erreur** automatique qu'Ansible affiche en cas d'entrée invalide.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ansible.builtin.ping
```

## ⚙️ Arborescence du lab

```text
labs/roles/argument-specs/
├── README.md                                ← ce fichier
├── Makefile                                 ← cible `clean`
├── roles/
│   └── webserver/
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       ├── defaults/main.yml
│       ├── meta/
│       │   ├── main.yml                     ← galaxy_info (lab 60)
│       │   └── argument_specs.yml           ← À ÉTUDIER (validation auto)
│       ├── vars/main.yml
│       └── templates/nginx.conf.j2
└── challenge/
    ├── README.md                            ← consigne du challenge
    └── tests/
        └── test_argument_specs.py
```

## 📚 Exercice 1 — Lire `meta/argument_specs.yml`

Ouvrez `roles/webserver/meta/argument_specs.yml` :

```yaml
argument_specs:
  main:
    short_description: "Installer et configurer nginx avec validation"
    description:
      - "Ce rôle installe nginx, le configure via un template, ..."
    author:
      - Stéphane Robert

    options:
      webserver_state:
        type: str
        default: present
        description: État du paquet
        choices:
          - present
          - absent
          - latest

      webserver_listen_port:
        type: int
        default: 80
        description: Port d'écoute HTTP (1-65535)

      webserver_service_enabled:
        type: bool
        default: true
        description: Démarrage automatique du service au boot
```

🔍 **Observation** — chaque option a au moins :

| Champ | Rôle |
| --- | --- |
| `type:` | Type Python attendu (`str`, `int`, `bool`, `list`, `dict`, `path`, `raw`) |
| `default:` | Valeur si non fournie. **Doit cohérer avec `defaults/main.yml`**. |
| `description:` | Documentation pour `ansible-doc -t role` |
| `choices:` (optionnel) | Liste de valeurs autorisées. Refuse toute autre. |
| `required:` (optionnel) | Si `true`, l'absence de la variable fait échouer le play |

**`main:`** est le nom du **point d'entrée** du rôle (`tasks/main.yml`). Si
votre rôle a plusieurs entry points (cf. `import_role/include_role` avec
`tasks_from:`), vous documentez chacune en parallèle dans `argument_specs:`.

## 📚 Exercice 2 — Tester avec une valeur valide

Créez un `playbook.yml` à la racine du lab qui utilise le rôle avec des
**valeurs valides** :

```yaml
---
- name: Test argument_specs avec valeurs valides
  hosts: db1.lab
  become: true
  roles:
    - role: webserver
      vars:
        webserver_listen_port: 8090
        webserver_state: present
        webserver_service_state: started
        webserver_index_content: "Argument specs validés !"
```

Lancez :

```bash
ansible-playbook labs/roles/argument-specs/playbook.yml
```

🔍 **Observation** : le play tourne **sans warning** sur les variables.
`argument_specs` a validé silencieusement.

## 📚 Exercice 3 — Tester avec une valeur INVALIDE

Modifiez `webserver_state` à `enabled` (qui n'est **pas** dans `choices`) :

```yaml
vars:
  webserver_state: enabled    # ← INVALIDE
```

Relancez :

```bash
ansible-playbook labs/roles/argument-specs/playbook.yml
```

🔍 **Observation** — sortie attendue (extrait) :

```text
TASK [webserver : Validating arguments against arg spec 'main'] ***
fatal: [db1.lab]: FAILED! => {
  "argument_errors": [
    "value of webserver_state must be one of: present, absent, latest, got: enabled"
  ],
  "msg": "Validation of arguments failed: ..."
}
```

L'erreur est :

- **Précoce** : avant la 1ère tâche du rôle.
- **Claire** : on sait exactement quelle variable et quelles valeurs sont autorisées.
- **Bloquante** : le rôle ne tourne pas du tout.

## 📚 Exercice 4 — Tester un type incorrect

Modifiez `webserver_listen_port` à `"abcd"` (string au lieu d'int) :

```yaml
vars:
  webserver_listen_port: "abcd"   # ← INVALIDE (pas un int)
```

🔍 **Observation** :

```text
"argument_errors": [
  "argument 'webserver_listen_port' is of type str and we were unable to convert to int"
]
```

`argument_specs` valide aussi les **conversions de type**. Une chaîne
numérique (`"8080"`) est convertie en int automatiquement, mais une chaîne
non-numérique fait échouer.

## 📚 Exercice 5 — Marquer une variable `required: true`

Ajoutez une option **obligatoire** dans `argument_specs.yml` :

```yaml
options:
  webserver_admin_email:
    type: str
    required: true
    description: Email de l'administrateur (obligatoire)
```

Relancez **sans définir** `webserver_admin_email`. Sortie :

```text
"argument_errors": [
  "missing required arguments: webserver_admin_email"
]
```

> 💡 **Bonne pratique** : limitez les `required: true` à ce qui n'a vraiment
> pas de défaut sensé. Préférez un `default:` qui marche dans la majorité
> des cas.

## 🔍 Observations à noter

- **`argument_specs` valide AVANT l'exécution** — erreur précoce et claire.
- **Pas d'argument_specs = validation tardive** dans une tâche obscure.
- **`type:`** force une vérification (et conversion automatique si
  possible). Préférez `int`, `bool`, `list`, `dict` à `str` quand pertinent.
- **`choices:`** est l'arme contre les fautes de frappe (`enabled` vs
  `present`).
- **Un fichier par entry point** : `argument_specs.yml` peut documenter
  plusieurs sections (`main:`, `install:`, `configure:` …).
- **`ansible-doc -t role <chemin>`** affiche la doc générée à partir
  d'`argument_specs.yml`. C'est gratuit dès qu'on a remplit ce fichier.
- **Profil production d'`ansible-lint`** exige `meta/argument_specs.yml` —
  un rôle sans est rejeté.

## 🤔 Questions de réflexion

1. Vous avez `defaults/main.yml: webserver_listen_port: 80` mais
   `argument_specs.yml: webserver_listen_port: { type: int, default: 8080 }`.
   Quelle valeur sera utilisée par défaut ? Pourquoi est-ce un piège ?

2. Vous voulez accepter **n'importe quelle string** pour `webserver_index_content`
   mais **refuser** les chaînes vides. Comment l'exprimer dans
   `argument_specs.yml` ? (Indice : `required: true`).

3. `argument_specs` ne valide pas les **plages numériques** (ex: port entre
   1 et 65535). Comment ajouter cette validation ? (Indice : combiner avec
   un `assert:` au début de `tasks/main.yml`.)

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`argument_specs` pour `tasks_from:`** : si votre rôle a un entry point
  alternatif (`tasks/install.yml`, `tasks/configure.yml`), documentez-les
  dans `argument_specs.yml: install:`, `argument_specs.yml: configure:`.
- **Plages avec `assert:`** : à la 1ère tâche du rôle, ajoutez un
  `assert: that: [webserver_listen_port > 0, webserver_listen_port <= 65535]`.
- **`mutually_exclusive`** dans une plus haute version d'Ansible : permet
  de déclarer que 2 options ne peuvent pas être utilisées ensemble.
- **Génération automatique de doc** : `ansible-doc -t role webserver` lit
  `argument_specs.yml` et formate la doc en CLI.

## 🔍 Linter avec `ansible-lint`

```bash
ansible-lint labs/roles/argument-specs/roles/webserver/
ansible-lint --profile production labs/roles/argument-specs/
```

Le profil `production` valide en particulier la **présence** et la **cohérence**
de `argument_specs.yml` avec `defaults/main.yml`.
