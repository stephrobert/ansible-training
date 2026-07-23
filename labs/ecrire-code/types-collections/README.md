# Lab 13 — Collection types (lists, dicts, nested)

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

🔗 [**Ansible collection types: list, dict, nested**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/types-collections/)

Beyond the simple types (string, int, bool), Ansible makes heavy use of
**complex structures**: lists (`[1, 2, 3]`), dictionaries (`{key: value}`), and
nested combinations (list of dicts, dict containing lists). These structures
are the foundation of **service inventories**, **multi-environment configs**, and
**structured loops**. Mastering the **`loop:` + `loop_control:`** pairing on these
collections is one of the RHCE EX294 markers.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Define** a list, a dict, and a **list of dicts** in YAML.
2. **Loop** over a list of dicts with `loop: + loop_control: label:`.
3. **Filter** a loop with `when:` on a dict field.
4. **Access** nested fields via dotted notation (`item.tags[0]`).
5. **Diagnose** a case where the expected structure does not match (typo, wrong level).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible web1.lab -m ping
ansible web1.lab -b -m shell -a "rm -f /tmp/service-*.txt /tmp/tag-*.txt"
```

## 📚 Exercise 1 — Simple list vs simple dict

Create `lab.yml`:

```yaml
---
- name: Demo types collections
  hosts: web1.lab
  become: true
  vars:
    # Simple list
    fruits:
      - pomme
      - banane
      - cerise

    # Simple dictionary
    db_config:
      host: db1.lab
      port: 5432
      name: myapp_db
  tasks:
    - name: Iterer sur la liste fruits
      ansible.builtin.debug:
        msg: "Fruit : {{ item }}"
      loop: "{{ fruits }}"

    - name: Acceder aux champs du dict
      ansible.builtin.debug:
        msg: "Connect to {{ db_config.host }}:{{ db_config.port }}/{{ db_config.name }}"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/types-collections/lab.yml
```

🔍 **Observation**:

- `loop: "{{ fruits }}"` → **3 iterations**, `item` is a string.
- `db_config.host` → dotted notation on a simple dict.

## 📚 Exercise 2 — List of dicts (the most common pattern)

Modify `lab.yml` to add a `services` variable:

```yaml
vars:
  services:
    - name: nginx
      port: 80
      enabled: true
      tags: [web, frontend]
    - name: redis
      port: 6379
      enabled: false
      tags: [cache, backend]
    - name: postgresql
      port: 5432
      enabled: true
      tags: [database, backend]
```

And the associated task:

```yaml
- name: Poser un marqueur par service active
  ansible.builtin.copy:
    dest: "/tmp/service-{{ item.name }}.txt"
    content: "Service {{ item.name }} sur port {{ item.port }}, tags={{ item.tags | join(',') }}\n"
    mode: "0644"
  loop: "{{ services }}"
  loop_control:
    label: "{{ item.name }}"
  when: item.enabled
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/types-collections/lab.yml
```

🔍 **Observation**:

- **3 iterations** but **2 changed** (nginx, postgresql) and **1 skipped** (redis, `enabled: false`).
- **`loop_control: label:`** displays `[item=nginx]` instead of the full dict: readable console output.
- **`item.tags | join(',')`**: turns the list of tags into the string `web,frontend`.

```bash
ansible web1.lab -b -m shell -a "ls /tmp/service-*.txt && cat /tmp/service-nginx.txt"
```

## 📚 Exercise 3 — Access nested fields

Test the **two equivalent notations** to access a dict field:

```yaml
- name: Comparer les deux notations d acces
  ansible.builtin.debug:
    msg: |
      Pointee : {{ services[0].name }}
      Bracket : {{ services[0]['name'] }}
      Nested  : {{ services[0].tags[1] }}
```

🔍 **Observation**: both notations give the same result. **When to prefer which?**

- **Dotted** (`var.key`): more readable, but does not work if the key contains a
  dash, a space, or starts with a digit (`var.my-key` ❌).
- **Bracket** (`var['key']`): always works, and accepts **expressions**
  (`var[dynamic_key_name]`).

**In practice**: dotted by default, bracket if the key contains special characters
or if the key is dynamic.

## 📚 Exercise 4 — Jinja2 filters on collections

On the list of dicts `services`, we want to **extract** only the enabled services
**in a simplified format**. The `selectattr` filter is the ideal tool.

```yaml
- name: Extraire les services actives en liste de noms
  ansible.builtin.debug:
    msg: "Actives : {{ services | selectattr('enabled') | map(attribute='name') | list }}"

- name: Filtrer par tag
  ansible.builtin.debug:
    msg: "Services backend : {{ services | selectattr('tags', 'contains', 'backend') | map(attribute='name') | list }}"
```

🔍 **Observation**:

- `selectattr('enabled')` keeps the dicts where `enabled` is truthy → `[nginx, postgresql]`.
- `map(attribute='name')` projects onto the `name` field → `['nginx', 'postgresql']`.
- `selectattr('tags', 'contains', 'backend')` keeps those whose `tags` contains `backend`
  → `[redis, postgresql]`.

Jinja2 filters on collections are covered in detail in **lab 19 (essential
filters)** and **lab 27 (advanced filters)**.

## 📚 Exercise 5 — The trap: wrong nesting level

Reproduce a classic error case. Modify the `services` variable:

```yaml
services:
  - name: nginx
    port: 80
    config:
      ssl_enabled: true
      certificate: /etc/ssl/cert.pem
```

And try:

```yaml
- name: Faux acces (typo niveau)
  ansible.builtin.debug:
    msg: "Cert: {{ services[0].certificate }}"  # ❌ certificate is under config
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/types-collections/lab.yml
```

🔍 **Observation**: error `'dict object' has no attribute 'certificate'`. The field
is under **`services[0].config.certificate`**, not directly under `services[0]`.

**Diagnostic tool**: use `ansible.builtin.debug: var: services[0]` to
**display the full structure** of an element before writing the accesses.

```yaml
- name: Diagnostiquer la structure
  ansible.builtin.debug:
    var: services[0]
```

## 🔍 Observations to note

- **List of dicts** = the most common pattern to describe a fleet (services, users, packages).
- **`loop_control: label:`** is mandatory in practice: unreadable output without it.
- **`when: item.<key>`** filters the iterations without a second loop.
- **Dotted vs bracket notation**: dotted by default, bracket for special / dynamic keys.
- **`selectattr` + `map(attribute=...)`** = the filtering / projection tool on lists of dicts.

## 🤔 Reflection questions

1. You have a list of 200 services. You want to act only on those whose `tags`
   contains both `backend` AND `production`. How do you express this filter?
   (hint: `selectattr` can be chained).

2. Why does `vars: my_dict: {}` (empty dict) generate an error if you try
   `my_dict.somekey`, whereas on a non-empty dict the same expression returns
   "undefined" without crashing?

3. Which structure would you choose to describe 50 users with their permissions:
   a **dict of dicts** (`users: {alice: {...}, bob: {...}}`) or a **list of dicts**
   (`users: [{name: alice, ...}, {name: bob, ...}]`)? What criteria?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`combine`**: merge two dicts. Useful to **layer** a base config
  with an override.
- **`dict2items`** + **`items2dict`**: convert a dict into a list of dicts (to loop
  over it) and back (to rebuild it after filtering).
- **`json_query`**: the Ansible-side equivalent of `jq`: for complex extractions
  on large JSON (output of a `uri:`).
- **`defaults + overrides` pattern**: `vars: { app: '{{ app_defaults | combine(app_overrides, recursive=True) }}' }`:
  layer a default config with a per-environment override.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/types-collections/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/types-collections/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/types-collections/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
