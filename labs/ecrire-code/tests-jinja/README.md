# Lab 28 — Tests Jinja2 (`is defined`, `is mapping`, `is sequence`, `is regex`)

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

🔗 [**Tests Jinja2 Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/tests-jinja/)

Les **tests Jinja2** s'écrivent avec **`is`** et retournent un booléen :
`{{ var is defined }}`, `{{ var is mapping }}`, `{{ var is regex }}`. Différents
des **filtres** (qui transforment), les tests **interrogent** une valeur.

Tests les plus utiles RHCE :

| Test | Vrai si... |
|---|---|
| `is defined` / `is undefined` | Variable existe / n'existe pas |
| `is none` | Variable existe mais vaut `None` (`null` YAML) |
| `is string` | Type `str` |
| `is mapping` | Type `dict` |
| `is sequence` | Liste, tuple, ou string |
| `is iterable` | Boucle possible (sequence + mapping) |
| `is number` / `is integer` / `is float` | Type numérique |
| `is regex` / `is match` / `is search` | Match d'une regex |
| `is in [list]` | Appartenance à une liste |
| `is divisibleby(n)` | Modulo |
| `is even` / `is odd` | Parité |

Les tests sont **chainables avec `not`** : `{{ var is not defined }}`.

## 🎯 Objectifs

À la fin de ce lab, vous saurez :

1. **Tester** la définition d'une variable (`is defined`, `is undefined`).
2. **Vérifier** le type (`is mapping`, `is sequence`, `is string`).
3. **Matcher** une regex avec `is match` (anchored) et `is search` (n'importe où).
4. **Tester** l'appartenance à une liste (`is in`).
5. **Combiner** tests dans des `when:` Ansible et `{% if %}` Jinja2.

## 🔧 Préparation

```bash
cd /home/bob/Projets/ansible-training
ansible db1.lab -m ping
```

## 📚 Exercice 1 — `is defined` / `is undefined`

Créez `lab.yml` :

```yaml
---
- name: Demo tests jinja2
  hosts: db1.lab
  vars:
    explicit_var: "hello"
    null_var: null
    # implicit_var n'est pas defini
  tasks:
    - name: explicit_var is defined
      ansible.builtin.debug:
        msg: "{{ explicit_var is defined }}"
        # → True

    - name: implicit_var is undefined
      ansible.builtin.debug:
        msg: "{{ implicit_var is undefined }}"
        # → True

    - name: null_var is defined (existe meme si vaut null)
      ansible.builtin.debug:
        msg: "defined : {{ null_var is defined }}, none : {{ null_var is none }}"
        # → defined : True, none : True
```

🔍 **Observation** :

- `is defined` est vrai même si la variable vaut `null`.
- Pour distinguer "absente" de "null", **combiner** `is defined and not is none`.

```yaml
when: my_var is defined and my_var is not none
```

## 📚 Exercice 2 — Tests de types

```yaml
- name: Demo tests de type
  vars:
    config_dict: {host: db1, port: 5432}
    config_list: [a, b, c]
    config_string: "hello"
    config_int: 42
    config_float: 3.14
  tasks:
    - name: Tester un dict
      ansible.builtin.debug:
        msg: "config_dict is mapping : {{ config_dict is mapping }}"
        # → True

    - name: Tester une liste
      ansible.builtin.debug:
        msg: "config_list is sequence and not string : {{ config_list is sequence and config_list is not string }}"
        # → True

    - name: Tester une string (sequence aussi en Python !)
      ansible.builtin.debug:
        msg: "config_string is string : {{ config_string is string }}, sequence : {{ config_string is sequence }}"
        # → string : True, sequence : True (piege)

    - name: Tester un int
      ansible.builtin.debug:
        msg: "config_int is integer : {{ config_int is integer }}, is number : {{ config_int is number }}"
```

🔍 **Observation** : **piège classique** : une string est aussi une `sequence` en
Python (itérable caractère par caractère). Donc `is sequence` matche aussi les
strings — il faut combiner `is sequence and is not string` pour vraiment tester
"liste/tuple".

## 📚 Exercice 3 — Tests de regex

```yaml
- name: Demo tests regex
  vars:
    hostname1: "web1.lab"
    hostname2: "db1.prod.example.com"
    log_line: "Connection from 192.168.1.42 on port 22"
  tasks:
    - name: is match (anchored, comme ^pattern$)
      ansible.builtin.debug:
        msg: "{{ hostname1 is match('^web\\d+\\.lab$') }}"
        # → True

    - name: is search (n importe ou dans la string)
      ansible.builtin.debug:
        msg: "{{ log_line is search('\\d+\\.\\d+\\.\\d+\\.\\d+') }}"
        # → True

    - name: is regex (alias de is match)
      ansible.builtin.debug:
        msg: "{{ hostname2 is regex('\\.prod\\.') }}"
        # → False (regex pas anchored doit matcher tout, sauf si .* explicit)

    - name: is regex avec .* implicite
      ansible.builtin.debug:
        msg: "{{ hostname2 is regex('.*\\.prod\\..*') }}"
        # → True
```

🔍 **Observation** :

- **`is match`** = anchored implicite (`^...$`) — comme Python `re.match`.
- **`is search`** = n'importe où dans la string — comme Python `re.search`.
- **`is regex`** = alias pour `is match` — donc anchored aussi.

Pour matcher une **partie** de la string, préférer `is search` ou ajouter `.*` autour.

## 📚 Exercice 4 — `is in [...]` (appartenance)

```yaml
- name: Demo is in
  vars:
    user_role: "admin"
    allowed_roles: [admin, manager, owner]
  tasks:
    - name: Tester appartenance
      ansible.builtin.debug:
        msg: "{{ user_role is in allowed_roles }}"
        # → True

    - name: Inverse
      ansible.builtin.debug:
        msg: "{{ user_role is not in ['readonly', 'guest'] }}"
        # → True
```

🔍 **Observation** : `is in` est plus lisible que `in` (Python natif) dans un
contexte Ansible. Équivalent fonctionnel à `{{ user_role in allowed_roles }}` mais
syntaxe **Test Jinja** explicite.

## 📚 Exercice 5 — Combinaison tests dans un `when:`

```yaml
- name: Tache conditionnee multi-tests
  ansible.builtin.debug:
    msg: "Validation OK"
  when:
    - app_config is defined
    - app_config is mapping
    - app_config.port is defined
    - app_config.port is integer
    - app_config.port > 1024
    - app_config.port < 65535
```

🔍 **Observation** : la **liste** sous `when:` = AND implicite. Cette tâche tourne
uniquement si **toutes** les conditions sont vraies. Pattern de **validation
défensive** : avant d'utiliser une variable complexe, on vérifie sa structure.

**Variante avec `assert:`** :

```yaml
- name: Valider la config app
  ansible.builtin.assert:
    that:
      - app_config is defined
      - app_config.port is integer
      - app_config.port > 1024
    fail_msg: "app_config.port doit etre un int > 1024"
    success_msg: "Config valide"
```

## 📚 Exercice 6 — Tests dans un template Jinja2

```jinja
{# templates/conditional.j2 #}
{% if app_config is defined and app_config is mapping %}
[app]
{% if app_config.host is defined %}
host = {{ app_config.host }}
{% endif %}
{% if app_config.port is defined and app_config.port is integer %}
port = {{ app_config.port }}
{% endif %}
{% else %}
# Config app non definie
{% endif %}
```

🔍 **Observation** : tests dans `{% if %}` permettent de **générer des templates
défensifs** — qui ne génèrent une section que si les variables nécessaires sont
définies et bien typées.

## 📚 Exercice 7 — Le piège : `is not defined` vs `is undefined`

```yaml
- name: Test 1 (forme courte)
  ansible.builtin.debug:
    msg: "ok"
  when: undefined_var is not defined

- name: Test 2 (forme equivalente)
  ansible.builtin.debug:
    msg: "ok"
  when: undefined_var is undefined
```

🔍 **Observation** : les deux formes sont **équivalentes**. La forme courte
(`is not defined`) est plus lisible. La forme `is undefined` est aussi correcte mais
moins fréquente.

**Attention** : `is none` ≠ `is undefined`. Une variable définie qui vaut `null`
passe `is defined: True` ET `is none: True`. Il faut distinguer.

## 🔍 Observations à noter

- **Tests Jinja2** = `var is test` — retourne un bool.
- **`is defined` / `is undefined`** = existence de la variable.
- **`is none`** = existe et vaut `null`.
- **`is mapping` / `is sequence` / `is string`** = tests de type — attention `string is sequence: True`.
- **`is match`** anchored, **`is search`** n'importe où, **`is regex`** alias de match.
- **`is in [list]`** = appartenance.
- **Combinaison dans `when:`** liste = AND implicite ; `assert:` pour validation explicite.

## 🤔 Questions de réflexion

1. Vous voulez tester si `app_config.tags` contient le tag `"production"`. Quel
   test (ou combinaison) utilisez-vous ?

2. Quelle est la différence entre `var is none` et `var | length == 0` pour une
   liste vide ?

3. Pourquoi `is match('lab')` matche-t-il `web1.lab` mais pas `lab.example.com` ?
   (indice : ancrage implicite).

## 🚀 Challenge final

Voir [`challenge/README.md`](challenge/README.md) pour la validation pytest+testinfra.

## 💡 Pour aller plus loin

- **Tests custom** : on peut écrire ses propres tests Python dans
  `plugins/test/mes_tests.py` (rare mais utile pour des tests métier).
- **`is callable`** : tester si une valeur est appelable (objet Python avec
  `__call__`). Marginal en Ansible.
- **Différence `is in` vs `in`** : `is in` est un test Jinja, `in` est un opérateur
  Python — les deux marchent dans Ansible mais `is in` est plus explicite.
- **Pattern `var | default(...) | type_debug`** : afficher le type final d'une
  variable après tous les filtres et défauts.
- **`assert:` + tests** : pattern de validation **fail fast** au début d'un play.

## 🔍 Linter avec `ansible-lint`

Avant de lancer pytest, validez la qualité de votre `lab.yml` et de votre
`challenge/solution.yml` avec **`ansible-lint`** :

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/tests-jinja/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/tests-jinja/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/tests-jinja/challenge/solution.yml
```

Si `ansible-lint` retourne `Passed: 0 failure(s), 0 warning(s)`, votre code
est conforme aux bonnes pratiques : FQCN explicite, `name:` sur chaque tâche,
modes de fichier en chaîne, idempotence respectée, modules dépréciés évités.

> 💡 **Astuce CI** : intégrez `ansible-lint --profile production` dans un hook
> pre-commit pour bloquer tout commit qui introduirait des anti-patterns.
