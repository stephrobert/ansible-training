# Lab 17 — Lookups (retrieve external data)

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

🔗 [**Ansible lookups: file, env, password, vars, hashi_vault**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/lookups/)

A **lookup** retrieves a piece of data from a **source external** to the playbook: a
local file, an environment variable, a shell command, a generated password, a
secret stored in Vault. **Execution happens on the control node**
(your machine), not the managed node, which is a crucial difference from classic
modules. The syntax: `{{ lookup('plugin_name', args) }}` or `query('plugin_name')`,
which always returns a list.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Read** the content of a local file with `lookup('file', ...)`.
2. **Retrieve** an environment variable with `lookup('env', ...)`.
3. **Run** a shell command on the control node with `lookup('pipe', ...)`.
4. **Generate** a password via `lookup('password', ...)`.
5. **Distinguish** `lookup` (returns 1 value or 1 string) from `query` (returns a list).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
mkdir -p labs/ecrire-code/lookups/files
ansible db1.lab -b -m shell -a "rm -f /tmp/lookup-*.txt"
```

## 📚 Exercise 1 — `lookup('file', ...)` read a local file

Create `files/welcome.txt`:

```text
Bienvenue dans l environnement RHCE 2026
Ansible Core 2.20 + ansible-navigator
```

Create `lab.yml`:

```yaml
---
- name: Demo lookup file
  hosts: db1.lab
  become: true
  tasks:
    - name: Lire le fichier local et le pousser sur db1
      ansible.builtin.copy:
        content: "{{ lookup('file', 'files/welcome.txt') }}"
        dest: /tmp/lookup-file.txt
        mode: "0644"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/lookups/lab.yml
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config db1.lab 'cat /tmp/lookup-file.txt'
```

🔍 **Observation**: the content of `files/welcome.txt` (on the control node) was
**read locally** by Ansible and **injected** into the `content:` of the `copy:`. The
local file **is never transferred** to db1: only its content as a string is used.

**Difference with `copy: src:`**: with `src:`, Ansible **transfers** the binary
file entirely. With `lookup('file', ...)`, you read the string and use it as a
Jinja2 variable. Handy to **inject** a file into a larger template.

## 📚 Exercise 2 — `lookup('env', ...)` environment variable

```yaml
- name: Lire l USER du control node
  ansible.builtin.debug:
    msg: "Vous etes connecte en tant que {{ lookup('env', 'USER') }}"

- name: Variable d env avec fallback si absente
  ansible.builtin.debug:
    msg: "MY_DEPLOY_KEY = {{ lookup('env', 'MY_DEPLOY_KEY') | default('non defini', true) }}"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/lookups/lab.yml
```

🔍 **Observation**: `USER` is defined in your shell, so it is displayed. `MY_DEPLOY_KEY`
is probably not defined → returns an **empty string** (not an error).
The filter `default('non defini', true)` (with `true` as the 2nd arg) treats the empty
string as "missing".

**Use case**: retrieve a CI token (`CI_JOB_TOKEN`), a path
(`HOME`), or a secret injected by Vault. Test locally:

```bash
MY_DEPLOY_KEY=secret123 ansible-playbook labs/ecrire-code/lookups/lab.yml
```

## 📚 Exercise 3 — `lookup('pipe', ...)` run a local command

```yaml
- name: Recuperer le SHA git du control node
  ansible.builtin.debug:
    msg: "Commit deploye : {{ lookup('pipe', 'git rev-parse --short HEAD 2>/dev/null || echo unknown') }}"

- name: Generer un timestamp local
  ansible.builtin.copy:
    content: "Deploy lance a {{ lookup('pipe', 'date --iso-8601=ns') }}\n"
    dest: /tmp/lookup-pipe.txt
    mode: "0644"
```

🔍 **Observation**: `pipe` runs the command **on the control node** and captures
stdout. The timestamp or the git SHA are **frozen at the moment of the run**, useful
to embed **traceability** in the deployed files.

**Security**: `pipe` runs any shell command. **Never** pass an unsanitized
user variable into `pipe`: risk of shell injection.

## 📚 Exercise 4 — `lookup('password', ...)` password generation

```yaml
- name: Generer un password persistant pour myapp
  ansible.builtin.set_fact:
    myapp_password: "{{ lookup('password', '/tmp/lookup-myapp-password.txt length=20 chars=ascii_letters,digits') }}"

- name: Afficher (a ne PAS faire en prod — log)
  ansible.builtin.debug:
    msg: "Generated password: {{ myapp_password }}"

- name: Pousser le password sur db1
  ansible.builtin.copy:
    content: "DB_PASSWORD={{ myapp_password }}\n"
    dest: /tmp/lookup-password-marker.txt
    mode: "0600"
```

🔍 **Observation**:

- **First run**: `lookup('password', ...)` **generates** a new password and
  **writes** it to `/tmp/lookup-myapp-password.txt` on the control node.
- **Subsequent runs**: `lookup` **reads** the existing file, the password stays
  **identical** across runs.

This is the **idempotent secret generation** pattern: generate once, persist,
reuse. Combined with **Ansible Vault** on the storage file, it is a simple
solution to manage passwords without WordPress / HashiCorp Vault.

## 📚 Exercise 5 — `lookup` vs `query`

```yaml
- name: lookup file (renvoie une string)
  ansible.builtin.debug:
    msg: "type lookup file : {{ lookup('file', 'files/welcome.txt') | type_debug }}"

- name: query lines (renvoie une liste — toujours)
  ansible.builtin.debug:
    msg: "type query lines : {{ query('lines', 'cat /etc/passwd') | type_debug }}"

- name: query file (renvoie une liste a 1 element)
  ansible.builtin.debug:
    msg: "type query file : {{ query('file', 'files/welcome.txt') | type_debug }}"
```

🔍 **Observation**:

- `lookup('file', ...)` → **string** (the file content).
- `query('lines', 'cat /etc/passwd')` → **list of lines**.
- `query('file', ...)` → **list of 1 element** (always a list, even if a single value).

**Rule**: use `query` when the result is used in a `loop:` (which wants a
list). Use `lookup` for a single value.

## 📚 Exercise 6 — The pitfall: `lookup` is run **each time** the variable is read

```yaml
- name: Lookup avec random — 1ere fois
  ansible.builtin.debug:
    msg: "uuid 1 : {{ lookup('pipe', 'uuidgen') }}"

- name: Lookup avec random — 2eme fois
  ansible.builtin.debug:
    msg: "uuid 2 : {{ lookup('pipe', 'uuidgen') }}"
```

🔍 **Observation**: the two UUIDs are **different**. Each evaluation of `{{
lookup(...) }}` re-runs the lookup.

**To freeze the value**: capture it in a `set_fact`:

```yaml
- name: Figer l uuid
  ansible.builtin.set_fact:
    deploy_uuid: "{{ lookup('pipe', 'uuidgen') }}"

- name: Reutiliser
  ansible.builtin.debug:
    msg: "Meme uuid partout : {{ deploy_uuid }} == {{ deploy_uuid }}"
```

## 🔍 Observations to note

- **Lookups run on the control node**, not the managed node.
- **`lookup` returns a value**, **`query` returns a list** (always).
- **`lookup('file', ...)`** = read a local file without transferring it.
- **`lookup('env', ...)`** = read an env variable of the control node.
- **`lookup('pipe', ...)`** = run a local shell command (mind the security).
- **`lookup('password', ...)`** = idempotent generation of a persisted password.
- **Lookups are re-evaluated** on each access, use `set_fact` to freeze.

## 🤔 Reflection questions

1. You want to inject the current **git commit SHA** into a file deployed on
   all the managed nodes for traceability. Lookup `file`, `env`, or `pipe`?

2. `lookup('password', '~/secrets.txt')` generates a persisted password. What
   is the **consequence** if several developers use this playbook from
   their machine? (hint: the file is local to the control node).

3. You want to read `/etc/passwd` from the **managed node** into an Ansible variable.
   `lookup('file', '/etc/passwd')` does not work (reads on the control node). What
   is the alternative?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`lookup('hashi_vault', 'secret=...')`**: retrieve a secret from HashiCorp
  Vault. Authentication via the `VAULT_TOKEN` env var.
- **`lookup('csvfile', ...)`**: extraction of a cell from a CSV, handy
  for business configs in a spreadsheet.
- **`lookup('template', ...)`**: render a Jinja2 template without deploying it,
  useful to pre-compute a file that you inject elsewhere.
- **`lookup('vars', 'dynamic_var_name')`**: dereference a variable whose
  name is itself dynamic (equivalent to `vars[var_name]`).
- **Custom plugin**: you can write your own lookup in Python (`plugins/lookup/mon_lookup.py`).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/lookups/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/lookups/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/lookups/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
