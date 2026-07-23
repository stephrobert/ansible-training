# Lab 18 — Jinja2 basic syntax (interpolation, logic, whitespace)

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

🔗 [**Jinja2 basic syntax in Ansible**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/jinja2-base/)

Jinja2 is the **templating engine** used by Ansible (and many other Python
tools: Flask, Django, Salt). It offers **3 syntaxes**:

- **`{{ expression }}`**: interpolation of an expression (variable, filter, computation).
- **`{% statement %}`**: logic (`for` loop, `if` condition, set, etc.).
- **`{# comment #}`**: jinja2 comment, **not rendered** in the output.

The **whitespace control** (`{%-`, `-%}`, `lstrip_blocks`, `trim_blocks`) manages
the appearance of spaces and line breaks around `{% %}` blocks, a classic pitfall
of generated config files.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Interpolate** variables with `{{ }}` and apply filters.
2. **Loop** with `{% for %}` and condition with `{% if %}`.
3. **Comment** with `{# #}` (jinja2) vs `#` (final-file comment).
4. **Master** the whitespace control (`{%- -%}`, `lstrip_blocks`, `trim_blocks`).
5. **Diagnose** a template that produces spurious line breaks.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
mkdir -p labs/ecrire-code/jinja2-base/templates
ansible db1.lab -b -m shell -a "rm -f /tmp/jinja-*.txt"
```

## 📚 Exercise 1 — Simple interpolation `{{ }}`

Create `templates/simple.j2`:

```jinja
Bonjour {{ name | default('inconnu') }} !
Vous avez {{ items | length }} items.
Premier item : {{ items[0] | upper }}.
```

Create `lab.yml`:

```yaml
---
- name: Demo jinja2 base
  hosts: db1.lab
  become: true
  vars:
    name: Alice
    items: [un, deux, trois]
  tasks:
    - name: Generer le fichier depuis le template simple
      ansible.builtin.template:
        src: templates/simple.j2
        dest: /tmp/jinja-simple.txt
        mode: "0644"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/jinja2-base/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /tmp/jinja-simple.txt'
```

🔍 **Observation**:

```text
Bonjour Alice !
Vous avez 3 items.
Premier item : UN.
```

`{{ }}` interpolates the expression. The **filters** (`| upper`, `| length`, `| default`)
apply just like in an Ansible `debug:`.

## 📚 Exercise 2 — Loops `{% for %}`

Create `templates/loop.j2`:

```jinja
[users]
{% for user in users %}
{{ user.name }} = {{ user.uid }}
{% endfor %}
```

Modify `lab.yml` to add:

```yaml
vars:
  users:
    - { name: alice, uid: 1001 }
    - { name: bob, uid: 1002 }
    - { name: charlie, uid: 1003 }
```

And the task:

```yaml
- name: Generer le fichier loop
  ansible.builtin.template:
    src: templates/loop.j2
    dest: /tmp/jinja-loop.txt
    mode: "0644"
```

**Run and inspect**:

```bash
ansible-playbook labs/ecrire-code/jinja2-base/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat -A /tmp/jinja-loop.txt'  # cat -A shows the line breaks
```

🔍 **Observation**: output (with `cat -A`):

```text
[users]$
$
alice = 1001$
$
bob = 1002$
$
charlie = 1003$
$
```

**Spurious empty lines** between iterations! This is the **whitespace pitfall**:
the `\n` after `{% for %}` stays in the output.

## 📚 Exercise 3 — Whitespace control with `{%- -%}`

Modify `templates/loop.j2` to add `-` in the jinja blocks:

```jinja
[users]
{% for user in users -%}
{{ user.name }} = {{ user.uid }}
{% endfor %}
```

🔍 **Observation**: `{%- ... -%}` removes spaces/line breaks **before** or
**after** the block. `{% for user in users -%}` removes the `\n` that would follow.
Cleaner output:

```text
[users]
alice = 1001
bob = 1002
charlie = 1003
```

**Convention**:

- **`{%-`** removes the whitespaces **before** the block.
- **`-%}`** removes the whitespaces **after** the block.

## 📚 Exercise 4 — `lstrip_blocks` and `trim_blocks` (global config)

Instead of putting `-` everywhere, you can enable these options **at the template
module level**:

```yaml
- name: Generer avec whitespace control auto
  ansible.builtin.template:
    src: templates/loop.j2
    dest: /tmp/jinja-loop-clean.txt
    mode: "0644"
    lstrip_blocks: true
    trim_blocks: true
```

| Option | Effect |
|---|---|
| **`trim_blocks: true`** | Removes the **first `\n` after** a `{% %}` block. |
| **`lstrip_blocks: true`** | Removes the **whitespaces before** a `{% %}` block (at the start of a line). |

🔍 **Observation**: with these two options, your template can be **indented**
cleanly (easy to read) without the indentation ending up in the output:

```jinja
{% for user in users %}
    {% if user.enabled %}
{{ user.name }} = {{ user.uid }}
    {% endif %}
{% endfor %}
```

The `    {% if %}` are **lstripped**, the `\n` after `{% endif %}` are **trim_blocked**.
Output identical to jinja2 without indentation.

**RHCE convention**: **always** `lstrip_blocks: true` + `trim_blocks: true` on
`template:` modules.

## 📚 Exercise 5 — Comments `{# #}` vs `#`

```jinja
{# This is a jinja2 comment, it will NOT be in the output #}
[server]
# This INI comment stays in the output
host = {{ ansible_default_ipv4.address }}
```

🔍 **Observation**: `{# #}` is a jinja2 comment (filtered at render). `#` is
just text (which ends up in the output). Use `{# #}` for **template notes**
that the end user should not see.

## 📚 Exercise 6 — Conditions `{% if %}` and `{% set %}`

```jinja
{% set environment = ansible_env.MYAPP_ENV | default('dev') %}
[app]
env = {{ environment }}

{% if environment == 'prod' %}
log_level = WARN
debug = false
{% elif environment == 'staging' %}
log_level = INFO
debug = false
{% else %}
log_level = DEBUG
debug = true
{% endif %}
```

🔍 **Observation**: `{% set %}` creates a variable **local to the template**. `{% if
elif else endif %}` allows classic branching. Handy to generate configs **tailored to
the environment** from a single template.

## 📚 Exercise 7 — The pitfall: `{{ }}` inside an Ansible `when:`

```yaml
# ❌ Wrong
- name: Action conditionnee
  ansible.builtin.debug:
    msg: "OK"
  when: "{{ ansible_distribution == 'AlmaLinux' }}"   # ❌

# ✅ Good
- name: Action conditionnee
  ansible.builtin.debug:
    msg: "OK"
  when: ansible_distribution == 'AlmaLinux'   # ✅
```

🔍 **Observation**: in `when:`, **no `{{ }}`**: the expression is already Jinja2.
Ansible 2.16+ shows a warning if you add the `{{ }}` anyway. This is a systematic
rule for `when:`, `failed_when:`, `changed_when:`, `loop_control: when:`.

## 🔍 Observations to note

- **`{{ expression }}`** = interpolation, **`{% statement %}`** = logic, **`{# comment #}`** = jinja2 note.
- **`{%- -%}`** (with dashes) = removes whitespaces around the block.
- **`lstrip_blocks: true`** + **`trim_blocks: true`** on `template:` = automatic whitespace control.
- **`{% set %}`** creates a variable local to the template.
- **No `{{ }}`** in `when:`, `failed_when:`, `changed_when:`.
- **`{# #}`** = jinja2 comment (filtered), **`#`** = final-file comment (kept).

## 🤔 Reflection questions

1. You generate an `/etc/hosts` file with a loop over `groups['all']`.
   Without `lstrip_blocks` and `trim_blocks`, what happens with your
   jinja2 indentation?

2. What is the semantic difference between `{% set x = expr %}` (in a template)
   and `set_fact: x: "{{ expr }}"` (in a play)?

3. You want to **keep the `\n`** after a `{% if %}` (because it is intentional).
   How do you override `trim_blocks: true` locally?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`{% include %}`**: include another `.j2` file in the current template.
  Lets you **factor out** reusable fragments (header, footer).
- **`{% extends %}`** + **`{% block %}`**: template inheritance (like Django).
  An extra layer for very large projects, often overkill for Ansible.
- **`{% raw %}` / `{% endraw %}`**: a zone where Jinja2 **does not interpret** `{{ }}`,
  useful when you generate a file that itself contains jinja2 (e.g. a
  Helm template that will be rendered later).
- **`autoescape: true`**: automatic escaping of HTML characters, useful
  only if you generate HTML with user data.
- **Jinja2 tests** (lab 28): `{% if x is defined %}`, `{% if x is mapping %}`, etc.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/jinja2-base/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/jinja2-base/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/jinja2-base/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
