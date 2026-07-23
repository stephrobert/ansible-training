# Lab 28 — Jinja2 Tests (`is defined`, `is mapping`, `is sequence`, `is regex`)

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

🔗 [**Ansible Jinja2 Tests**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/tests-jinja/)

**Jinja2 tests** are written with **`is`** and return a boolean:
`{{ var is defined }}`, `{{ var is mapping }}`, `{{ var is regex }}`. Unlike
**filters** (which transform), tests **query** a value.

The most useful RHCE tests:

| Test | True if... |
|---|---|
| `is defined` / `is undefined` | Variable exists / does not exist |
| `is none` | Variable exists but is `None` (YAML `null`) |
| `is string` | Type `str` |
| `is mapping` | Type `dict` |
| `is sequence` | List, tuple, or string |
| `is iterable` | Loop possible (sequence + mapping) |
| `is number` / `is integer` / `is float` | Numeric type |
| `is regex` / `is match` / `is search` | Regex match |
| `is in [list]` | Membership in a list |
| `is divisibleby(n)` | Modulo |
| `is even` / `is odd` | Parity |

Tests are **chainable with `not`**: `{{ var is not defined }}`.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Test** whether a variable is defined (`is defined`, `is undefined`).
2. **Check** the type (`is mapping`, `is sequence`, `is string`).
3. **Match** a regex with `is match` (anchored) and `is search` (anywhere).
4. **Test** membership in a list (`is in`).
5. **Combine** tests in Ansible `when:` and Jinja2 `{% if %}`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
```

## 📚 Exercise 1 — `is defined` / `is undefined`

Create `lab.yml`:

```yaml
---
- name: Demo tests jinja2
  hosts: db1.lab
  vars:
    explicit_var: "hello"
    null_var: null
    # implicit_var is not defined
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

🔍 **Observation**:

- `is defined` is true even if the variable is `null`.
- To distinguish "absent" from "null", **combine** `is defined and not is none`.

```yaml
when: my_var is defined and my_var is not none
```

## 📚 Exercise 2 — Type tests

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
        # → string : True, sequence : True (trap)

    - name: Tester un int
      ansible.builtin.debug:
        msg: "config_int is integer : {{ config_int is integer }}, is number : {{ config_int is number }}"
```

🔍 **Observation**: **classic trap**: a string is also a `sequence` in
Python (iterable character by character). So `is sequence` also matches
strings, you must combine `is sequence and is not string` to really test
"list/tuple".

## 📚 Exercise 3 — Regex tests

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
        # → False (regex not anchored must match everything, unless .* explicit)

    - name: is regex avec .* implicite
      ansible.builtin.debug:
        msg: "{{ hostname2 is regex('.*\\.prod\\..*') }}"
        # → True
```

🔍 **Observation**:

- **`is match`** = implicit anchoring (`^...$`), like Python `re.match`.
- **`is search`** = anywhere in the string, like Python `re.search`.
- **`is regex`** = alias for `is match`, so anchored too.

To match **part** of the string, prefer `is search` or add `.*` around it.

## 📚 Exercise 4 — `is in [...]` (membership)

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

🔍 **Observation**: `is in` is more readable than `in` (native Python) in an
Ansible context. Functionally equivalent to `{{ user_role in allowed_roles }}`
but with explicit **Jinja Test** syntax.

## 📚 Exercise 5 — Combining tests in a `when:`

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

🔍 **Observation**: the **list** under `when:` = implicit AND. This task runs
only if **all** conditions are true. **Defensive validation** pattern: before
using a complex variable, you check its structure.

**Variant with `assert:`**:

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

## 📚 Exercise 6 — Tests in a Jinja2 template

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
# App config not defined
{% endif %}
```

🔍 **Observation**: tests in `{% if %}` let you **generate defensive
templates**, ones that only render a section if the required variables are
defined and correctly typed.

## 📚 Exercise 7 — The trap: `is not defined` vs `is undefined`

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

🔍 **Observation**: both forms are **equivalent**. The short form
(`is not defined`) is more readable. The `is undefined` form is also correct but
less common.

**Warning**: `is none` ≠ `is undefined`. A defined variable that is `null`
passes `is defined: True` AND `is none: True`. You must distinguish them.

## 🔍 Observations to note

- **Jinja2 tests** = `var is test`, returns a bool.
- **`is defined` / `is undefined`** = variable existence.
- **`is none`** = exists and is `null`.
- **`is mapping` / `is sequence` / `is string`** = type tests, beware `string is sequence: True`.
- **`is match`** anchored, **`is search`** anywhere, **`is regex`** alias of match.
- **`is in [list]`** = membership.
- **Combining in `when:`** a list = implicit AND; `assert:` for explicit validation.

## 🤔 Reflection questions

1. You want to test whether `app_config.tags` contains the tag `"production"`.
   Which test (or combination) do you use?

2. What is the difference between `var is none` and `var | length == 0` for an
   empty list?

3. Why does `is match('lab')` match `web1.lab` but not `lab.example.com`?
   (hint: implicit anchoring).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Custom tests**: you can write your own Python tests in
  `plugins/test/mes_tests.py` (rare but useful for business-specific tests).
- **`is callable`**: test whether a value is callable (Python object with
  `__call__`). Marginal in Ansible.
- **Difference `is in` vs `in`**: `is in` is a Jinja test, `in` is a Python
  operator. Both work in Ansible but `is in` is more explicit.
- **Pattern `var | default(...) | type_debug`**: display the final type of a
  variable after all filters and defaults.
- **`assert:` + tests**: **fail fast** validation pattern at the start of a play.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/tests-jinja/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/tests-jinja/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/tests-jinja/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
