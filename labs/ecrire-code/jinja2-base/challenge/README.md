# 🎯 Challenge — MOTD template with `if` + `for`

## ✅ Objective

Generate **`/etc/motd-challenge`** on **db1.lab** from a Jinja2 template,
with a conditional block and a loop.

## 🧩 Files to create

### 1) `challenge/templates/motd.j2`

The template must use:

- **`{{ inventory_hostname }}`** to interpolate the host name
- **`{% if host_role == "DB" %}` … `{% endif %}`** to conditionally display
  a `Profil : DB` line
- **`{% for s in services %}` … `{% endfor %}`** to iterate over the list of
  services
- **Whitespace control**: use `{%- ... -%}` or `{%- ... %}` to avoid
  spurious empty lines

Skeleton:

```jinja
==========================================
  Bienvenue sur {{ ??? }}
==========================================
{% if ??? %}
Profil : DB
{% endif %}
Services :
{% for ??? in ??? %}
  - {{ ??? }}
{% endfor %}
```

### 2) `challenge/solution.yml`

Skeleton:

```yaml
---
- name: Challenge - Jinja2 base
  hosts: db1.lab
  become: true

  vars:
    host_role: DB
    services:
      - postgresql
      - chronyd
      - firewalld

  tasks:
    - name: Générer /etc/motd-challenge depuis le template
      ansible.builtin.template:
        src: ???
        dest: ???
        mode: "0644"
```

## 🧩 Expected output

```text
==========================================
  Bienvenue sur db1.lab
==========================================
Profil : DB
Services :
  - postgresql
  - chronyd
  - firewalld
```

> 💡 **Pitfalls**:
>
> - **`{{ ... }}` vs `{% ... %}`**: `{{ }}` evaluates and displays, `{% %}`
>   controls (if, for, set). Classic confusion: using `{{ if }}`
>   instead of `{% if %}`.
> - **`{% for ... %}` adds newlines**: use `{%- for -%}`
>   (with dashes) to remove the surrounding line breaks. Watch the
>   formatting of the produced file.
> - **`| default(...)`**: essential to make a template
>   reusable. Without it, a missing variable crashes the templating.
> - **Template path**: relative to `<role>/templates/` for a role,
>   or `templates/` next to the playbook otherwise. **Not** `template:
>   src: /absolute/path`.

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/jinja2-base/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/motd-challenge"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/jinja2-base/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-jinja2-base
```

## 💡 Going further

- **`trim_blocks` and `lstrip_blocks`**: template options that control the
  spaces around the `{%- %}` tags. Enable them on the module for a rendering
  that is more predictable:

  ```yaml
  ansible.builtin.template:
    trim_blocks: true
    lstrip_blocks: true
  ```

- **Conditional variables**: `{{ var | default('default_value') }}` in
  the template, to avoid `is undefined` everywhere.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/jinja2-base/challenge/solution.yml
   ```
