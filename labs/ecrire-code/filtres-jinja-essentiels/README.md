# Lab 19 — Filtres Jinja2 essentiels (`default`, `combine`, `selectattr`, `map`)

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

🔗 [**Filtres Jinja2 essentiels Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/filtres-jinja-essentiels/)

Les filtres Jinja2 transforment une valeur via la syntaxe **`{{ valeur | filtre }}`**.
Ansible expose les filtres standard de Jinja2 + ses propres filtres custom. Les
**10 filtres incontournables** RHCE forment 80% de l'usage quotidien :

| Catégorie | Filtres |
|---|---|
| Sécurité | `default`, `mandatory` |
| Strings | `upper`, `lower`, `title`, `regex_replace`, `replace`, `trim` |
| Listes | `unique`, `union`, `difference`, `intersect`, `length`, `sort` |
| Dicts | `dict2items`, `items2dict`, `combine` |
| Filtrage | `selectattr`, `rejectattr`, `map`, `select`, `reject` |
| Sérialisation | `to_json`, `to_yaml`, `to_nice_yaml`, `from_json`, `from_yaml` |

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Appliquer** `default()` pour gérer les variables absentes ou vides.
2. **Manipuler** des listes (unique, union, difference, sort).
3. **Filtrer** une liste de dicts avec `selectattr` + `map(attribute=...)`.
4. **Fusionner** deux dicts avec `combine` (avec ou sans `recursive`).
5. **Sérialiser** une variable en JSON/YAML pour debug ou export.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
```

## 📚 Exercice 1 — `default()` (gérer l'absence)

```yaml
---
- name: Demo filtres essentiels
  hosts: db1.lab
  vars:
    explicit_value: "defini"
    empty_value: ""
    # undefined_value n'est PAS defini
  tasks:
    - name: default — variable absente
      ansible.builtin.debug:
        msg: "{{ undefined_value | default('absent') }}"

    - name: default — variable vide (sans le 2eme arg)
      ansible.builtin.debug:
        msg: "{{ empty_value | default('absent') }}"

    - name: default — variable vide AVEC le 2eme arg true (force "vide" = absent)
      ansible.builtin.debug:
        msg: "{{ empty_value | default('absent', true) }}"

    - name: mandatory — echec controlé si absente
      ansible.builtin.debug:
        msg: "{{ undefined_value | mandatory }}"
      ignore_errors: true
```

🔍 **Observation** :

- `default('absent')` sur une variable **absente** → `absent`.
- `default('absent')` sur une variable **vide** (`""`) → `""` (vide reste vide !).
- `default('absent', true)` (avec `true` comme 2e arg) → `absent` même sur string vide.
- `mandatory` lance une erreur si la variable est absente — utile en début de play
  pour valider des prérequis.

## 📚 Exercice 2 — Filtres sur les listes

```yaml
- name: Demo listes
  vars:
    fruits: [pomme, banane, cerise, banane, fraise]
    legumes: [carotte, salade, banane]
  block:
    - name: unique
      ansible.builtin.debug:
        msg: "{{ fruits | unique }}"
        # → [pomme, banane, cerise, fraise]

    - name: union
      ansible.builtin.debug:
        msg: "{{ fruits | union(legumes) }}"
        # → [pomme, banane, cerise, fraise, carotte, salade]

    - name: difference (fruits qui ne sont pas legumes)
      ansible.builtin.debug:
        msg: "{{ fruits | difference(legumes) }}"
        # → [pomme, cerise, fraise]

    - name: intersect (commun)
      ansible.builtin.debug:
        msg: "{{ fruits | intersect(legumes) }}"
        # → [banane]

    - name: sort
      ansible.builtin.debug:
        msg: "{{ fruits | sort }}"

    - name: length
      ansible.builtin.debug:
        msg: "Nombre : {{ fruits | length }}"
```

🔍 **Observation** : ces filtres sont l'**équivalent des opérations d'ensembles**
en mathématiques. Ils sont à connaître pour manipuler des **listes d'utilisateurs**,
**listes de paquets**, **listes de tags**.

## 📚 Exercice 3 — Filtres sur les listes de dicts (`selectattr` + `map`)

```yaml
- name: Demo filtres listes de dicts
  vars:
    users:
      - { name: alice, role: admin, enabled: true }
      - { name: bob, role: user, enabled: true }
      - { name: charlie, role: admin, enabled: false }
      - { name: dave, role: user, enabled: true }
  block:
    - name: selectattr — admins seulement
      ansible.builtin.debug:
        msg: "{{ users | selectattr('role', 'equalto', 'admin') | list }}"

    - name: rejectattr — non-admins
      ansible.builtin.debug:
        msg: "{{ users | rejectattr('role', 'equalto', 'admin') | list }}"

    - name: selectattr + map — noms des admins
      ansible.builtin.debug:
        msg: "{{ users | selectattr('role', 'equalto', 'admin') | map(attribute='name') | list }}"
        # → [alice, charlie]

    - name: selectattr enabled — chainage de filtres
      ansible.builtin.debug:
        msg: "{{ users | selectattr('enabled') | selectattr('role', 'equalto', 'admin') | map(attribute='name') | list }}"
        # → [alice]  (admins ET enabled)
```

🔍 **Observation** : `selectattr` + `map(attribute=...)` est **la combinaison la
plus utilisée** sur les listes de dicts. Le **chaînage** permet d'appliquer plusieurs
filtres successifs (équivalent SQL `WHERE x AND y`).

**Variantes** : `selectattr('field')` (sans 2e arg) garde les éléments où le champ
est **truthy** (équivalent `WHERE field IS TRUE`).

## 📚 Exercice 4 — Filtres sur les dicts (`combine`, `dict2items`)

```yaml
- name: Demo filtres dicts
  vars:
    base_config:
      host: db1.lab
      port: 5432
      pool_size: 10
    overrides:
      port: 6432
      timeout: 30
  block:
    - name: combine — fusion simple (overrides gagne)
      ansible.builtin.debug:
        var: base_config | combine(overrides)
        # → {host: db1.lab, port: 6432, pool_size: 10, timeout: 30}

    - name: dict2items — convertir en liste pour boucler
      ansible.builtin.debug:
        msg: "{{ base_config | dict2items }}"
        # → [{key: host, value: db1.lab}, {key: port, value: 5432}, ...]

    - name: items2dict — l inverse (apres filtrage)
      ansible.builtin.debug:
        msg: "{{ base_config | dict2items | rejectattr('key', 'equalto', 'pool_size') | items2dict }}"
        # → {host: db1.lab, port: 5432}
```

**`combine` avec dicts imbriqués** (`recursive=True`) :

```yaml
- name: combine recursive
  vars:
    base:
      app:
        name: myapp
        config:
          host: localhost
          port: 80
    override:
      app:
        config:
          port: 8080  # On veut JUSTE override le port, garder host
  block:
    - name: Sans recursive (ecrase tout app.config)
      ansible.builtin.debug:
        var: base | combine(override)

    - name: Avec recursive (merge intelligent)
      ansible.builtin.debug:
        var: base | combine(override, recursive=True)
```

🔍 **Observation** :

- Sans `recursive=True`, `app.config` est **remplacé entièrement** → on perd `host: localhost`.
- Avec `recursive=True`, le merge descend dans les sous-dicts → on garde `host:
  localhost` et on ajoute/écrase `port: 8080`.

## 📚 Exercice 5 — Sérialisation (`to_json`, `to_nice_yaml`)

```yaml
- name: Demo serialisation
  vars:
    config:
      app: myapp
      ports: [80, 443]
      env: prod
  tasks:
    - name: to_json (compact)
      ansible.builtin.debug:
        msg: "{{ config | to_json }}"

    - name: to_nice_json (indented)
      ansible.builtin.debug:
        msg: "{{ config | to_nice_json(indent=2) }}"

    - name: to_yaml (pour debug)
      ansible.builtin.debug:
        msg: "{{ config | to_nice_yaml }}"

    - name: from_json — parser un JSON depuis un command:
      vars:
        json_string: '{"version": "1.0", "tags": ["v1", "stable"]}'
      ansible.builtin.debug:
        var: json_string | from_json
```

🔍 **Observation** : `to_*` et `from_*` sont essentiels pour :

- **Debug** : afficher une variable Ansible en YAML lisible.
- **Export** : générer un fichier JSON déployé sur le managed node.
- **Import** : parser la sortie d'un `command:` qui retourne du JSON.

## 📚 Exercice 6 — Le piège : `default` vs `default(omit)`

Sur les modules avec arguments optionnels, `default(omit)` est le pattern correct
pour **ne pas passer l'argument** quand la variable est absente.

```yaml
- name: Pattern correct avec default(omit)
  ansible.builtin.copy:
    src: files/config.txt
    dest: /tmp/lookup-default.txt
    owner: "{{ file_owner | default(omit) }}"
    group: "{{ file_group | default(omit) }}"
    mode: "{{ file_mode | default('0644') }}"
```

🔍 **Observation** :

- `mode: "{{ file_mode | default('0644') }}"` → si `file_mode` est absent, mode = `0644`.
- `owner: "{{ file_owner | default(omit) }}"` → si `file_owner` est absent, **l'argument
  `owner:` n'est pas passé du tout** au module.

**Sans `omit`**, `default('')` passerait `owner: ""` au module → erreur "owner can't be empty".

## 🔍 Observations à noter

- **`default(value, true)`** : 2e arg `true` traite la string vide comme absente.
- **`mandatory`** : échec contrôlé si la variable est absente — pour valider des prérequis.
- **`selectattr` + `map(attribute=...)`** = combinaison la plus utilisée sur listes de dicts.
- **`combine(recursive=True)`** = merge profond de dicts imbriqués.
- **`default(omit)`** = ne pas passer l'argument plutôt que passer une string vide.
- **`to_nice_yaml`** = outil de debug n°1 pour afficher une variable lisiblement.

## 🤔 Questions de réflexion

1. Vous voulez extraire les **emails** des utilisateurs admin d'une liste de dicts
   `users: [{name, role, email}]`. Quel pipeline de filtres ?

2. Vous fusionnez `defaults: {a: 1, b: 2}` avec `overrides: {b: 99, c: 3}`. Sans
   `recursive=True`, le résultat est `{a: 1, b: 99, c: 3}`. Quand `recursive=True`
   change-t-il quelque chose ?

3. `lookup('file', 'config.json') | from_json` vs `lookup('file', 'config.yml') |
   from_yaml` — quelle est la différence avec un simple `vars_files: - config.yml` ?

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **`json_query`** : équivalent de `jq` côté Ansible — pour des extractions complexes
  type `data.items[?status=='active'].id`. Voir lab 27 (filtres avancés).
- **`regex_replace`** : substitution par regex — `{{ 'web1.lab' | regex_replace('\\..*$', '') }}` → `web1`.
- **`b64encode` / `b64decode`** : pour préparer un secret à passer dans un header HTTP
  ou stocker dans un manifest Kubernetes.
- **`ipaddr`** : suite de filtres pour manipuler des IP/CIDR — `{{ '192.168.1.0/24'
  | ipaddr('first_usable') }}` → `192.168.1.1`. Nécessite `ansible.utils`.
- **Pattern `var | trim`** : éliminer les espaces / `\n` accidentels — TOUT capture
  de `register: r.stdout` devrait passer par `| trim`.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/filtres-jinja-essentiels/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
