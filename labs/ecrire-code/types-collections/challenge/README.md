# 🎯 Challenge — Filter a list of dicts with `selectattr`

## ✅ Objective

Write `challenge/solution.yml` that on **db1.lab**:

1. Declares in `vars:` a **list of dicts** `services` (4 services).
2. Writes `/tmp/services-production.txt` that contains **only** the services
   of the `production` tier, in the format `<name>:<port>` (one per line).

## 🧩 Input data

To copy into the play's `vars:`:

```yaml
services:
  - { name: api, port: 8080, tier: production }
  - { name: web, port: 80, tier: staging }
  - { name: cache, port: 6379, tier: production }
  - { name: dev-db, port: 5432, tier: dev }
```

## 🧩 Expected output

The `/tmp/services-production.txt` file must contain **exactly**:

```text
api:8080
cache:6379
```

The `web` (staging) and `dev-db` (dev) services are **excluded**.

## 🧩 Jinja2 tools to know

Three filters to combine to process a list of dicts:

| Filter | Effect |
| --- | --- |
| `selectattr('attr', 'equalto', 'value')` | Keeps the elements where `attr == value` |
| `map(attribute='name')` | Extracts the `name` field from each element |
| `join(',')` | Concatenates a list into a string |

> 💡 Here we want to **filter** on `tier == "production"`, then iterate
> in a `content:` template to produce `<name>:<port>` line by line.
> You can do this with a **Jinja2 loop** (`{% for ... %}`) directly
> in the `content:` string.

## 🧩 Skeleton

```yaml
---
- name: Challenge - filtrer services production
  hosts: ???
  become: ???

  vars:
    services:
      # ... copy the list above ...

  tasks:
    - name: Poser /tmp/services-production.txt (production seulement)
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          {% for s in services | ??? %}
          {{ s.??? }}:{{ s.??? }}
          {% endfor %}
```

> 💡 **Traps**:
>
> - **Jinja2 loop in `content:`**: use `{% for ... %}` (with `%`,
>   not `{{ }}` which is for simple evaluation).
> - **`selectattr` returns a generator**, not a list: be sure to chain
>   with `| list` if you want `length` or to index.
> - **YAML indentation**: the `content: |` (block scalar) preserves the
>   raw structure. The `{% for %}` can stay at the start of the line, which
>   is readable but introduces a line break between items. That is OK
>   for this challenge.
> - **Exact test**: the output must contain `api:8080` AND `cache:6379`,
>   and **NOT** `web:80` nor `dev-db:5432`. Double-check the syntax
>   `selectattr('tier', 'equalto', 'production')`.

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/types-collections/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/services-production.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/types-collections/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-types-collections
```

## 💡 Going further

- **Without `selectattr`**: reproduce the filter with a `for` + `if`
  (`{% for s in services if s.tier == "production" %}`). It is more verbose
  but useful when you have several complex conditions.
- **Sorting**: add a `| sort(attribute='port')` after `selectattr` to sort
  by ascending port number.
- **`dict2items` lookup**: to iterate over a dict of dicts rather than
  a list of dicts.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/types-collections/challenge/solution.yml
   ```
