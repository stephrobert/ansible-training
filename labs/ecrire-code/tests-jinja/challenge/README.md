# 🎯 Challenge — Jinja2 tests in a conditional file

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**, drops `/tmp/tests-jinja.txt`
containing 4 lines, each produced by a different **Jinja2 test** (`is
defined`, `is mapping`, `is sequence`, `is undefined`).

## 🧩 Input data

```yaml
user: { name: alice, age: 30 }
config:
  app: nginx
  port: 80
ports: [80, 443, 8080]
# optional_var is intentionally not defined
```

## 🧩 Expected output

```text
user_defined=yes
config_mapping=yes
ports_sequence=yes
optional_undefined=yes
```

Each line appears **only if** its corresponding test returns true.

## 🧩 The 4 Jinja2 tests to use

| Test | True if… |
| --- | --- |
| `is defined` | the variable exists (as opposed to `is undefined`) |
| `is mapping` | the value is a dict (`{}`) |
| `is sequence` | the value is a list (`[]`) or a tuple |
| `is undefined` | the variable was never defined |

> ⚠️ **Filter** vs **test** difference: **filters** go after `|`
> (`var | upper`), **tests** go after `is` (`var is defined`). Do not swap them.

## 🧩 Skeleton

```yaml
---
- name: Challenge - tests Jinja2
  hosts: db1.lab
  become: true

  vars:
    user: { name: alice, age: 30 }
    config:
      app: nginx
      port: 80
    ports: [80, 443, 8080]

  tasks:
    - name: Poser /tmp/tests-jinja.txt avec lignes conditionnelles
      ansible.builtin.copy:
        dest: ???
        mode: "0644"
        content: |
          {% if ??? %}user_defined=yes
          {% endif %}
          {%- if ??? %}config_mapping=yes
          {% endif %}
          {%- if ??? %}ports_sequence=yes
          {% endif %}
          {%- if ??? %}optional_undefined=yes
          {% endif %}
```

> 💡 **Whitespace control**: the `{%- ... %}` (with a leading dash) strip the
> whitespace before the tag. This is what avoids an empty line between each
> `{% if %}` … `{% endif %}`.

**Pitfalls**:

> - **Jinja tests**: `is defined`, `is mapping`, `is sequence`, `is
>   string`, `is number`, `is divisibleby(N)`, `is even/odd`.
> - **`is mapping`** matches a **dict** (not a list). `is sequence`
>   matches a list OR a tuple OR a range, but also a **string**
>   (each character). Checking `is iterable` is broader.
> - **`is defined`** vs **`is none`**: `defined` = the variable exists.
>   `is not none` = it exists AND its value is not `null`.
> - **`is divisibleby`**: `42 is divisibleby 7` → `true`. Useful for
>   selective iterations (every 5th element, etc.).

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/tests-jinja/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/tests-jinja.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/tests-jinja/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-tests-jinja
```

## 💡 Going further

- **Numeric tests**: `is even`, `is odd`, `is divisibleby(N)`.
- **String tests**: `is iterable`, `is string`, `is integer`, `is float`,
  `is boolean`.
- **`is failed` / `is changed` / `is succeeded`** on a `register:` result,
  extremely useful in `when:`.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/tests-jinja/challenge/solution.yml
   ```
