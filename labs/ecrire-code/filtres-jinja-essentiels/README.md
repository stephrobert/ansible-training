# Lab 19 — Essential Jinja2 filters (`default`, `combine`, `selectattr`, `map`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root (see
> [root README](../../../README.md#-démarrage-rapide) for the details).

## 🧠 Recap

🔗 [**Essential Jinja2 filters in Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/filtres-jinja-essentiels/)

Jinja2 filters transform a value via the **`{{ value | filter }}`** syntax.
Ansible exposes the standard Jinja2 filters + its own custom filters. The
**10 must-know** RHCE filters make up 80% of daily use:

| Category | Filters |
|---|---|
| Security | `default`, `mandatory` |
| Strings | `upper`, `lower`, `title`, `regex_replace`, `replace`, `trim` |
| Lists | `unique`, `union`, `difference`, `intersect`, `length`, `sort` |
| Dicts | `dict2items`, `items2dict`, `combine` |
| Filtering | `selectattr`, `rejectattr`, `map`, `select`, `reject` |
| Serialization | `to_json`, `to_yaml`, `to_nice_yaml`, `from_json`, `from_yaml` |

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Apply** `default()` to handle missing or empty variables.
2. **Manipulate** lists (unique, union, difference, sort).
3. **Filter** a list of dicts with `selectattr` + `map(attribute=...)`.
4. **Merge** two dicts with `combine` (with or without `recursive`).
5. **Serialize** a variable to JSON/YAML for debug or export.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
```

## 📚 Exercise 1 — `default()` (handle absence)

```yaml
---
- name: Demo filtres essentiels
  hosts: db1.lab
  vars:
    explicit_value: "defini"
    empty_value: ""
    # undefined_value is NOT defined
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

🔍 **Observation**:

- `default('absent')` on a **missing** variable → `absent`.
- `default('absent')` on an **empty** variable (`""`) → `""` (empty stays empty!).
- `default('absent', true)` (with `true` as the 2nd arg) → `absent` even on an empty string.
- `mandatory` raises an error if the variable is missing, useful at the start of a
  play to validate prerequisites.

## 📚 Exercise 2 — Filters on lists

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

🔍 **Observation**: these filters are the **equivalent of set operations**
in mathematics. They are worth knowing to manipulate **user lists**,
**package lists**, **tag lists**.

## 📚 Exercise 3 — Filters on lists of dicts (`selectattr` + `map`)

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
        # → [alice]  (admins AND enabled)
```

🔍 **Observation**: `selectattr` + `map(attribute=...)` is **the most used
combination** on lists of dicts. **Chaining** lets you apply several successive
filters (SQL equivalent `WHERE x AND y`).

**Variants**: `selectattr('field')` (without a 2nd arg) keeps the elements where
the field is **truthy** (equivalent to `WHERE field IS TRUE`).

## 📚 Exercise 4 — Filters on dicts (`combine`, `dict2items`)

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

**`combine` with nested dicts** (`recursive=True`):

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
          port: 8080  # We want to override ONLY the port, keep host
  block:
    - name: Sans recursive (ecrase tout app.config)
      ansible.builtin.debug:
        var: base | combine(override)

    - name: Avec recursive (merge intelligent)
      ansible.builtin.debug:
        var: base | combine(override, recursive=True)
```

🔍 **Observation**:

- Without `recursive=True`, `app.config` is **replaced entirely** → we lose `host: localhost`.
- With `recursive=True`, the merge descends into the sub-dicts → we keep `host:
  localhost` and add/overwrite `port: 8080`.

## 📚 Exercise 5 — Serialization (`to_json`, `to_nice_yaml`)

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

🔍 **Observation**: `to_*` and `from_*` are essential for:

- **Debug**: display an Ansible variable as readable YAML.
- **Export**: generate a JSON file deployed on the managed node.
- **Import**: parse the output of a `command:` that returns JSON.

## 📚 Exercise 6 — The pitfall: `default` vs `default(omit)`

On modules with optional arguments, `default(omit)` is the correct pattern
to **not pass the argument** when the variable is missing.

```yaml
- name: Pattern correct avec default(omit)
  ansible.builtin.copy:
    src: files/config.txt
    dest: /tmp/lookup-default.txt
    owner: "{{ file_owner | default(omit) }}"
    group: "{{ file_group | default(omit) }}"
    mode: "{{ file_mode | default('0644') }}"
```

🔍 **Observation**:

- `mode: "{{ file_mode | default('0644') }}"` → if `file_mode` is missing, mode = `0644`.
- `owner: "{{ file_owner | default(omit) }}"` → if `file_owner` is missing, **the argument
  `owner:` is not passed at all** to the module.

**Without `omit`**, `default('')` would pass `owner: ""` to the module → error "owner can't be empty".

## 🔍 Observations to note

- **`default(value, true)`**: the 2nd arg `true` treats the empty string as missing.
- **`mandatory`**: controlled failure if the variable is missing, to validate prerequisites.
- **`selectattr` + `map(attribute=...)`** = the most used combination on lists of dicts.
- **`combine(recursive=True)`** = deep merge of nested dicts.
- **`default(omit)`** = not passing the argument rather than passing an empty string.
- **`to_nice_yaml`** = the number one debug tool to display a variable readably.

## 🤔 Reflection questions

1. You want to extract the **emails** of the admin users from a list of dicts
   `users: [{name, role, email}]`. What filter pipeline?

2. You merge `defaults: {a: 1, b: 2}` with `overrides: {b: 99, c: 3}`. Without
   `recursive=True`, the result is `{a: 1, b: 99, c: 3}`. When does `recursive=True`
   change anything?

3. `lookup('file', 'config.json') | from_json` vs `lookup('file', 'config.yml') |
   from_yaml`: what is the difference with a simple `vars_files: - config.yml`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`json_query`**: Ansible's equivalent of `jq`, for complex extractions
  like `data.items[?status=='active'].id`. See lab 27 (advanced filters).
- **`regex_replace`**: substitution by regex, `{{ 'web1.lab' | regex_replace('\\..*$', '') }}` → `web1`.
- **`b64encode` / `b64decode`**: to prepare a secret to pass in an HTTP header
  or store in a Kubernetes manifest.
- **`ipaddr`**: a set of filters to manipulate IP/CIDR, `{{ '192.168.1.0/24'
  | ipaddr('first_usable') }}` → `192.168.1.1`. Requires `ansible.utils`.
- **`var | trim` pattern**: eliminate accidental spaces / `\n`. EVERY capture
  of `register: r.stdout` should go through `| trim`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/filtres-jinja-essentiels/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
