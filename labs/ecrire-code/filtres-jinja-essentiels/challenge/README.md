# The data comes in dirty, the config must come out clean

## The situation

The values feeding your configs arrive from three sources and none of them
agrees with the others. One field comes padded with spaces and shouting in
capitals. Two package lists overlap and must become a single set. The service
catalogue mixes prod and staging. A base config needs a TLS override stacked on
top. And one variable is sometimes plainly absent — which does not warn you, it
kills the templating halfway through the run.

You clean all of it **in the data**, on `db1.lab`, from **control-node.lab**.

Your mission:

1. Normalise a dirty string, then merge two package lists into one
   deduplicated, sorted set.
2. Extract the **production** services from a list of dicts and keep only their
   names.
3. Merge a base config with its overrides, and understand what a flat merge
   does to the keys underneath.
4. Make a missing variable **fall back** to a value instead of taking the run
   down with it, then write the six results on db1.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/filtres-jinja-essentiels/ (in French)

## 🎯 Challenge — 6 Jinja2 filters in a marker file

### ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**, writes
`/tmp/filtres-result.txt` containing **6 lines**, each demonstrating an essential
Jinja2 filter.

### 🧩 Input data

Put these variables in the play's `vars:`:

```yaml
raw_input: "  HELLO World  "
pkgs_a: ["nginx", "redis", "postgres"]
pkgs_b: ["redis", "memcached"]
services:
  - { name: api, port: 8080, env: prod }
  - { name: web, port: 80, env: staging }
  - { name: cache, port: 6379, env: prod }
base_config:
  app: api
  port: 80
tls_overrides:
  port: 443
  tls: true
```

### 🧩 Expected output

```text
trimmed=hello world
union=memcached,nginx,postgres,redis
prod_services=api,cache
merged=app=api port=443 tls=True
default_value=fallback-OK
yaml_safe={hello: world}
```

### 🧩 6 filters to use

| Line | Filters | Effect |
| --- | --- | --- |
| `trimmed` | `trim`, `lower` | Spaces removed + lowercase |
| `union` | `+`, `unique`, `sort`, `join(',')` | List concatenation, dedup, sort, join |
| `prod_services` | `selectattr('env', 'equalto', 'prod')`, `map(attribute='name')`, `sort`, `join(',')` | Filter + extraction + sort + join |
| `merged` | `combine(...)` then sorted `key=value` serialization | Dict merge |
| `default_value` | `default('fallback-OK')` | Default value on a nonexistent variable |
| `yaml_safe` | `to_yaml`, `trim` | Inline YAML rendering |

### 🧩 Skeleton

```yaml
---
- name: Challenge - 6 filtres Jinja2
  hosts: db1.lab
  become: true

  vars:
    # ... copy the 5 variables above ...

  tasks:
    - name: Poser /tmp/filtres-result.txt
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          trimmed={{ raw_input | ??? | ??? }}
          union={{ ??? }}
          prod_services={{ ??? }}
          merged={{ ??? }}
          default_value={{ ??? }}
          yaml_safe={{ {'hello': 'world'} | ??? | trim }}
```

> 💡 **Hint for `merged`**: `(base_config | combine(tls_overrides)).items()`
> returns a list of tuples `(key, value)`. You can then
> `map('join', '=')` to turn each tuple into `key=value`, then
> `sort | join(' ')` to order and concatenate.

**Pitfalls**:

> - **`combine`** is recursive (deep merge) only with
>   `recursive=true`. Otherwise it does a flat merge (the right-hand dict
>   completely overwrites the left-hand dict).
> - **`map('attribute=...')`** vs **`map('extract', dict)`**: the first
>   extracts an attribute from each element, the second extracts by key.
>   Classic confusion.
> - **`| default([])`** on a list: essential before `length` or
>   iteration if the variable may be missing.
> - **`to_yaml` / `to_json` / `to_nice_yaml`**: YAML/JSON output. The
>   `nice` version adds indentation and line breaks (to produce a readable
>   file).

### 🚀 Run

```bash
ansible-playbook labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/filtres-result.txt"
```

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/filtres-jinja-essentiels/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-filtres-jinja-essentiels
```

### 💡 Going further

- **`difference` / `intersect` / `symmetric_difference`**: set operations
  on lists (beyond `union`).
- **`regex_replace`**: substitute a pattern. Example: `{{ "v1.2.3" |
  regex_replace('^v', '') }}` → `1.2.3`.
- **`to_nice_json` / `to_nice_yaml`**: indented serialization for more
  readable files.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/filtres-jinja-essentiels/challenge/solution.yml
   ```
