# 🎯 Challenge — `lineinfile` vs `template` (the 2 approaches)

## ✅ Objective

On **db1.lab**, demonstrate **two opposite philosophies** to manage a
configuration file:

- **`lineinfile`** = **surgical**, you touch **one line** without rewriting the
  rest of the file (ideal for `/etc/hosts`, `/etc/sysctl.conf`, etc.).
- **`template`** = **full owner**, you **rewrite** the whole file
  from a Jinja2 template (ideal for configs generated in full, like a business
  `/etc/nginx/nginx.conf`).

## 🧩 Task 1 — `lineinfile` on `/etc/hosts`

Add a **single line** in `/etc/hosts`:

```text
192.168.99.99 mon-host.lab
```

Without touching the other existing lines.

Hints:

- `path:` → the file to modify.
- `line:` → the content of the line.
- `regexp:` → to make the operation idempotent: if a line matching the
  pattern already exists, it is **replaced** (not duplicated).
- `state: present` (default).

## 🧩 Task 2 — `template` on `/etc/myapp.conf`

Create `challenge/templates/myapp.conf.j2` that produces:

```ini
[server]
host = 0.0.0.0
port = 8080
workers = 4

[database]
url = postgres://db1.lab/myapp
pool_size = 10
```

Source variables (to put in the play's `vars:`):

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  workers: 4
database:
  url: "postgres://db1.lab/myapp"
  pool_size: 10
```

The template must interpolate **each** value from these dicts (e.g.
`{{ server.host }}`, `{{ database.pool_size }}`).

## 🧩 Skeleton

```yaml
---
- name: "Challenge - lineinfile vs template"
  hosts: db1.lab
  become: true

  vars:
    server:
      # ...
    database:
      # ...

  tasks:
    - name: Ajouter une entrée DNS via lineinfile
      ansible.builtin.lineinfile:
        path: ???
        regexp: ???
        line: ???
        state: present

    - name: Générer /etc/myapp.conf depuis le template
      ansible.builtin.template:
        src: ???
        dest: ???
        mode: "0644"
```

> 💡 **Pitfalls**:
>
> - **`lineinfile`** = modify **one line** in an existing file
>   (e.g. `/etc/hosts`, `/etc/sshd_config`). If the line is not
>   matched by `regexp:`, it is **added** at the end.
> - **`template`** = replace **the whole file**. Idempotent by
>   checksum, so no drift.
> - **When to prefer `lineinfile`**: modify 1-3 lines in a file
>   managed by a package (do not overwrite the default values).
> - **When to prefer `template`**: you own the whole file
>   (in-house app config, motd, banner). More readable and auditable.
> - **`blockinfile`** (lab 33): in between, manages a **marked
>   block** in an existing file.

## 🚀 Run

```bash
ansible-playbook labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "grep mon-host /etc/hosts"
ansible db1.lab -m ansible.builtin.command -a "cat /etc/myapp.conf"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/lineinfile-vs-template/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-lineinfile-vs-template
```

## 💡 Going further

- **When to use `lineinfile` vs `template`?**
  - **`lineinfile`**: config managed by several sources (Ansible + another
    tool + admin), or a default config you do not control (e.g.
    `/etc/sshd_config` shipped by the package).
  - **`template`**: config 100% managed by Ansible (no other source of
    truth). More predictable, more testable.
- **`blockinfile`** (lab 33): in between. Manages a **block** delimited by
  markers. Ideal when you want to add a section without touching the rest.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/lineinfile-vs-template/challenge/solution.yml
   ```
