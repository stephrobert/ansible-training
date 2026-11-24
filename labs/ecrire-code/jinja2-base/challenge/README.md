# A login banner that lies about the machine

## The situation

Every host greets you with a banner someone typed by hand years ago. Half of
them still advertise a service that was decommissioned two reorganisations
ago, one welcomes you to a hostname that no longer exists, and they are all
peppered with stray blank lines left by a previous attempt at generating them.
Ops wants one banner: generated, correct on every host, and readable.

You start with **db1.lab**, from **control-node.lab**.

Your mission:

1. Render `/etc/motd-challenge` from a **Jinja2 template**, the host naming
   itself from the inventory instead of from a literal string.
2. Show the role line **only when** the host actually carries that role: a
   conditional inside the template, not two templates side by side.
3. List the host's services with a **loop** driven by a variable, one per line.
4. Kill the stray blank lines with **whitespace control**: that is the whole
   difference between a generated banner and a banner that looks generated.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/jinja2-base/ (in French)

## 🎯 Challenge — MOTD template with `if` + `for`

### ✅ Objective

Generate **`/etc/motd-challenge`** on **db1.lab** from a Jinja2 template,
with a conditional block and a loop.

### 🧩 Files to create

#### 1) `challenge/templates/motd.j2`

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

#### 2) `challenge/solution.yml`

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

### 🧩 Expected output

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

### 🚀 Run

```bash
ansible-playbook labs/ecrire-code/jinja2-base/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/motd-challenge"
```

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/jinja2-base/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-jinja2-base
```

### 💡 Going further

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
