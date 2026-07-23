# 🎯 Challenge — Module `template:` with `backup`

## ✅ Objective

Generate **`/etc/banner.txt`** on **db1.lab** from a template, with
**mode 0644**. Adding `backup: true` is a **production best practice**,
recommended but **not verified by the tests**.

## 🧩 Files to create

### 1) `challenge/templates/banner.txt.j2`

Must produce:

```text
====================
Bienvenue !
====================
Generated: 2026-04-25
Owner: ops-team
```

Jinja2 hints:

- `{{ motd_text }}` interpolates a variable.
- `{% for k, v in metadata.items() %}` iterates over a dict (key-value pairs).
- `{{ k | capitalize }}` puts the first letter in uppercase (`generated` to
  `Generated`).

Skeleton:

```jinja
====================
{{ ??? }}
====================
{% for ???, ??? in metadata.items() %}
{{ ??? | capitalize }}: {{ ??? }}
{% endfor %}
```

### 2) `challenge/solution.yml`

Skeleton:

```yaml
---
- name: Challenge - module template avec backup
  hosts: db1.lab
  become: true

  vars:
    motd_text: "Bienvenue !"
    metadata:
      generated: "2026-04-25"
      owner: "ops-team"

  tasks:
    - name: Générer /etc/banner.txt depuis le template
      ansible.builtin.template:
        src: ???
        dest: ???
        mode: "0644"
        backup: true              # best practice (prod), not verified by the tests
```

## 🧩 Options to know on `template:`

| Option | Effect |
| --- | --- |
| `src:` | Path **relative to the playbook** or absolute. Convention: `templates/<name>.j2`. |
| `dest:` | Path **on the managed node**. |
| `mode: "0644"` | Unix permissions (as a string, not bare octal). |
| `backup: true` | Backs up the previous version as `<dest>.<timestamp>~` before overwriting. |
| `validate: 'cmd %s'` | Validates the syntax before writing (e.g. `nginx -t -c %s`). |
| `trim_blocks: true` | Removes the `\n` after `{% %}`. |
| `lstrip_blocks: true` | Removes the start-of-line spaces before `{% %}`. |

> 💡 **Traps**:
>
> - **`backup: true`** creates a backup `<dest>.<timestamp>~` before
>   overwriting. A production best practice for critical configs, **not
>   verified by the tests** (on the first run, nothing to save).
> - **`validate:`**: command to validate the file **before** writing it.
>   If it fails, the original file stays intact. Format:
>   `validate: 'sshd -t -f %s'` (the `%s` is replaced by a temporary
>   file).
> - **`trim_blocks` + `lstrip_blocks`**: essential for readable
>   templates. Without them, your `{% if %}` leave empty lines
>   and stray spaces.
> - **`mode:` always quoted**: `mode: "0644"` (not `mode: 0644` which is
>   octal then decimal = mode 420).

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/module-template/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /etc/banner.txt"
ansible db1.lab -m ansible.builtin.command -a "ls -la /etc/banner.txt*"
```

🔍 On the **2nd run after modifying** the template, you will see `/etc/banner.txt.<ts>~`
appear (proof of `backup: true`).

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/module-template/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-module-template
```

## 💡 Going further

- **`validate:`**: add `validate: 'echo %s'` to see Ansible pass the
  temporary file to the validation command. On an nginx.conf, it would be
  `nginx -t -c %s`. If the validation fails, the original file stays
  intact.
- **`force: false`**: prevents the overwrite if the file already exists
  (the opposite of the default).
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/module-template/challenge/solution.yml
   ```
