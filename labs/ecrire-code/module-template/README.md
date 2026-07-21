# Lab 29 — Module `template:` (`validate`, `backup`, `lstrip_blocks`)

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

🔗 [**Ansible template module: validate, backup, lstrip_blocks**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/templates-jinja2/module-template/)

`ansible.builtin.template:` generates a file on the managed node from a Jinja2
template on the control node plus Ansible variables. It is the **number 1** module
for configuration files: nginx.conf, postgresql.conf, sshd_config,
prometheus.yml.

Key differences with `copy:`:

- **`template:`** renders the Jinja2 (interpolation, filters, conditions, loops).
- **`copy:`** transfers the content **as-is** (no interpolation).

Critical RHCE options:

- **`validate:`**: validates the syntax **before** overwriting the target.
- **`backup: true`**: backs up the previous version.
- **`lstrip_blocks: true`** + **`trim_blocks: true`**: whitespace control.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Generate** a config file from a Jinja2 template.
2. **Validate** the syntax before writing (critical pattern for `sshd_config`, `nginx.conf`).
3. **Back up** automatically with `backup: true`.
4. **Master** whitespace control via `lstrip_blocks` + `trim_blocks`.
5. **Apply** best practices (mode, owner, group) for deployed configs.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
mkdir -p labs/ecrire-code/module-template/templates
ansible db1.lab -b -m shell -a "rm -f /etc/myapp.conf*; rm -f /tmp/lab-template-*"
```

## 📚 Exercise 1 — First template

Create `templates/myapp.conf.j2`:

```jinja
[server]
host = {{ server.host }}
port = {{ server.port }}
workers = {{ server.workers }}

[database]
url = {{ database.url }}
pool_size = {{ database.pool_size }}
```

Create `lab.yml`:

```yaml
---
- name: Demo template basique
  hosts: db1.lab
  become: true
  vars:
    server:
      host: "0.0.0.0"
      port: 8080
      workers: 4
    database:
      url: "postgres://db1.lab/myapp"
      pool_size: 10
  tasks:
    - name: Generer myapp.conf depuis template
      ansible.builtin.template:
        src: templates/myapp.conf.j2
        dest: /etc/myapp.conf
        owner: root
        group: root
        mode: "0644"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/module-template/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /etc/myapp.conf'
```

🔍 **Observation**: the template was **rendered** (variables interpolated, INI
sections generated). Compared to `copy:`, you could not have done that with a
static file.

## 📚 Exercise 2 — `backup: true` (automatic backup)

Modify `lab.yml` to add `backup: true`:

```yaml
- name: Generer avec backup
  ansible.builtin.template:
    src: templates/myapp.conf.j2
    dest: /etc/myapp.conf
    backup: true
    owner: root
    group: root
    mode: "0644"
```

**Modify the template** (change `port: 8080` to `port: 9090`) then rerun:

```bash
ansible-playbook labs/ecrire-code/module-template/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'ls -la /etc/myapp.conf*'
```

🔍 **Observation**: a `myapp.conf.<timestamp>~` file is created before the overwrite.
Format: `<dest>.<YYYY-MM-DD@HH:MM:SS~>`. Handy for a **quick rollback**:

```bash
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'sudo cp /etc/myapp.conf.2026-04-25@21:00:00~ /etc/myapp.conf'
```

**`backup: true`** is free (just a local cp), **always** enable it on critical
config files.

## 📚 Exercise 3 — `validate:` (reject an invalid config)

Critical pattern for `sshd_config`, `nginx.conf`, `sudoers`: a malformed file
locks the system.

**SSH case**: sshd no longer starts if `sshd_config` is invalid, so you lose SSH
access to the server.

```yaml
- name: Generer sshd_config avec validation
  ansible.builtin.template:
    src: templates/sshd_config.j2
    dest: /etc/ssh/sshd_config
    backup: true
    owner: root
    group: root
    mode: "0600"
    validate: 'sshd -t -f %s'
  notify: Reload sshd

handlers:
  - name: Reload sshd
    ansible.builtin.systemd_service:
      name: sshd
      state: reloaded
```

🔍 **Observation**:

- **`validate: 'sshd -t -f %s'`**: Ansible **renders** the template into a
  temporary file, runs `sshd -t -f /tmp/<temp>` to check the syntax.
- If `sshd -t` returns **0** (OK), the config is written, the handler is notified.
- If `sshd -t` returns **!= 0** (invalid), the temporary file is discarded,
  `/etc/ssh/sshd_config` stays **intact**, the task **fails**.

**The `%s`** is replaced by the path of the temporary file. **Mandatory** in the
validation command.

**nginx case**: `validate: 'nginx -t -c %s'`.
**sudoers case**: `validate: 'visudo -cf %s'`.

## 📚 Exercise 4 — `lstrip_blocks` + `trim_blocks` (whitespace control)

Create `templates/loop.j2`:

```jinja
[users]
{% for user in users %}
    {% if user.enabled %}
{{ user.name }} = {{ user.uid }}
    {% endif %}
{% endfor %}
```

Without whitespace control, the render will include the stray indentation and
line breaks. With it:

```yaml
- name: Template avec whitespace control
  ansible.builtin.template:
    src: templates/loop.j2
    dest: /tmp/lab-template-clean.txt
    mode: "0644"
    lstrip_blocks: true
    trim_blocks: true
```

🔍 **Observation**:

- **`lstrip_blocks: true`**: removes the spaces **before** the `{% %}` blocks at the start of a line.
- **`trim_blocks: true`**: removes the `\n` **after** the `{% %}` blocks.

Combined, you can **indent your template** for readability without the
indentation ending up in the output. Clean output:

```text
[users]
alice = 1001
charlie = 1003
```

**RHCE convention**: **always** enable these two options.

## 📚 Exercise 5 — `copy:` + `content:` vs `template:`

Question: when to prefer one over the other?

```yaml
# copy + content: no interpolation, for VERY short files
- ansible.builtin.copy:
    content: "Static content\n"
    dest: /tmp/static.txt

# template: interpolation, for config files
- ansible.builtin.template:
    src: templates/dynamic.j2
    dest: /tmp/dynamic.txt
```

| Case | Recommended module |
|---|---|
| Short static file (1-3 lines, no variable) | `copy: content:` |
| Long static file without variable | `copy: src:` |
| File with **1 interpolated variable** | `template:` |
| File with loops, conditions, filters | `template:` (mandatory) |

🔍 **Observation**: if you have **a single** `{{ var }}`, switch to `template:`.
The cost is nil, the benefit is **scalability** (later you will add other
interpolations).

## 📚 Exercise 6 — The trap: undefined variables in a template

```jinja
{# templates/strict.j2 #}
[app]
host = {{ app_host }}
port = {{ app_port }}
debug = {{ app_debug }}
```

If a single variable is missing (`app_debug` undefined), Jinja2 **crashes** with:

```text
'app_debug' is undefined
```

**Solution 1**: `default()` in the template.

```jinja
debug = {{ app_debug | default(false) }}
```

**Solution 2**: `assert:` at the start of the play to validate all the variables.

```yaml
- ansible.builtin.assert:
    that:
      - app_host is defined
      - app_port is defined and app_port is integer
      - app_debug is defined
    fail_msg: "Variables app_* manquantes"
```

**Solution 3**: play-level `vars:` with default values.

🔍 **Observation**: prefer `assert:` + explicit variables. An **early and clear**
failure is better than a cryptic error in the middle of the template.

## 🔍 Observations to note

- **`template:`** renders the Jinja2; **`copy:`** transfers without interpretation.
- **`backup: true`** = free safety net, always enable on critical configs.
- **`validate:`** = mandatory pattern for `sshd_config`, `nginx.conf`, `sudoers`.
- **`lstrip_blocks: true`** + **`trim_blocks: true`** = standard whitespace control.
- **`mode: "0644"`** (with quotes), otherwise YAML parses `0644` as decimal.
- **Undefined variables** in a template lead to a render error. Use `default()` or `assert:`.

## 🤔 Reflection questions

1. You generate `/etc/sshd_config` via `template:`. Why is `validate: 'sshd -t -f
   %s'` **more important** here than on `/etc/motd`?

2. `template:` rewrites the file **completely** on every run. What is the risk on
   a file that the **user** modifies manually (user config vs managed config)?

3. Can `lstrip_blocks: true` + `trim_blocks: true` introduce a bug if your
   template has **deliberately** significant spaces / `\n`? Give an example.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`block_start_string` / `block_end_string`**: change the `{% %}` delimiters to
  generate a file that **itself** contains jinja2 (e.g. a Helm chart).
- **`force: false`**: does not rewrite if the file already exists, for initial
  configs the operator may modify.
- **`template + lineinfile` pattern**: `template:` for the base, `lineinfile:`
  for one-off overrides the operator may add. Do not mix them, otherwise
  `template:` overwrites everything.
- **`vault_decrypt` at runtime**: a template can contain
  `{{ lookup('vault_password_files', 'mypassword') }}` to inject a decrypted
  Vault secret at render time.
- **Lab 30 (lineinfile vs template)**: detailed comparison of the two approaches.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/module-template/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/module-template/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/module-template/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
