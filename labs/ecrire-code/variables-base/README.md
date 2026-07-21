# Lab 12 — Variables (declaration and scopes)

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

🔗 [**Ansible variables: declaration, scopes and simple types**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/variables-base/)

Ansible offers **5 main locations** to declare a variable: `vars:` (in the
play), `vars_files:` (external files), `group_vars/`, `host_vars/`, and
`--extra-vars` (CLI). Each location has a different **priority**: understanding
these priorities is crucial to avoid being surprised when a variable "does not
take the expected value".

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Declare** a variable at play level (`vars:`).
2. **Externalize** variables into a file (`vars_files:`).
3. **Override** from the CLI with `--extra-vars` and observe absolute priority.
4. **Distinguish** simple types (string, int, float, bool) and their YAML pitfalls.
5. **Diagnose** a case where a variable does not take the expected value.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
mkdir -p labs/ecrire-code/variables-base/vars
ansible web1.lab -m ping
```

## 📚 Exercise 1 — Variable at play level (`vars:`)

Create `lab.yml`:

```yaml
---
- name: Demo vars du play
  hosts: web1.lab
  become: true
  vars:
    app_version: "1.0"
    app_env: "dev"
  tasks:
    - name: Afficher les variables
      ansible.builtin.debug:
        msg: "version={{ app_version }} env={{ app_env }}"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml
```

🔍 **Observation**: the debug output shows `version=1.0 env=dev`. These variables
exist **only for this play**: another play in the same file would not see them.

## 📚 Exercise 2 — Externalize into `vars_files:`

Create `vars/app.yml`:

```yaml
---
app_port: 80
app_protocol: "http"
app_replicas: 3
```

Modify `lab.yml` to add `vars_files:`:

```yaml
---
- name: Demo vars + vars_files
  hosts: web1.lab
  become: true
  vars:
    app_version: "1.0"
    app_env: "dev"
  vars_files:
    - vars/app.yml
  tasks:
    - name: Afficher toutes les variables
      ansible.builtin.debug:
        msg: |
          version={{ app_version }}
          env={{ app_env }}
          port={{ app_port }}
          protocol={{ app_protocol }}
          replicas={{ app_replicas }}
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml
```

🔍 **Observation**: the variables from `vars_files:` are **loaded in addition** to
the play's `vars:`: no conflict, complementarity. **Why externalize?**

- Reuse the same file across multiple plays.
- Version business configs (DEV/STAGING/PROD) in separate files.
- Let an operator modify `vars/app.yml` without touching the playbook.

## 📚 Exercise 3 — Override with `--extra-vars` (absolute priority)

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml \
  --extra-vars "app_env=prod app_version=2.0"
```

🔍 **Observation**: `app_env` and `app_version` changed (`prod`, `2.0`), but
`app_port` stays at `80`, `app_protocol` at `http`, `app_replicas` at `3` (you
did not override them).

**`--extra-vars` (level 22)** is the **absolute priority** in Ansible
precedence. No other location can override it. It is the **production
troubleshooting weapon**: an operator forces a precise value without modifying
the code.

**Useful variants** of `--extra-vars`:

```bash
# JSON (for complex values)
--extra-vars '{"app_env":"prod","app_version":"2.0","tags":["v2","stable"]}'

# From a file
--extra-vars "@vars/prod-override.yml"
```

## 📚 Exercise 4 — YAML pitfalls on types

YAML is strict but sometimes surprising. Create `vars/types.yml`:

```yaml
---
# Simple string
app_name: "myapp"

# Integer (no quotes)
app_port: 8080

# Boolean (yes/no rejected in strict YAML 1.2, use true/false)
app_debug: true

# Float
app_ratio: 0.5

# String that LOOKS LIKE a number, quotes mandatory otherwise the leading 0 is lost
app_id: "0042"

# String that looks like a boolean (classic trap)
app_yes_no: "yes"  # Without quotes, becomes bool true in YAML 1.1
```

Modify `lab.yml` to load `vars/types.yml` and display the types via the
`type_debug` filter:

```yaml
- name: Afficher type Python de chaque variable
  ansible.builtin.debug:
    msg: "{{ item }} = {{ vars[item] | type_debug }}"
  loop:
    - app_name
    - app_port
    - app_debug
    - app_ratio
    - app_id
    - app_yes_no
```

🔍 **Observation**:

- `app_name` → `str` (string)
- `app_port` → `int` (integer, not string!)
- `app_debug` → `bool`
- `app_ratio` → `float`
- `app_id` → `str` (the quotes preserved "0042")
- `app_yes_no` → `str` (because we used quotes)

**Without quotes** on `app_id`, you would get `int 42` (loss of the leading
`00`): a classic. On `app_yes_no` without quotes, `bool True` instead of
`str "yes"`.

## 📚 Exercise 5 — Real case: why doesn't my variable have the right value?

Reproduce a common pitfall. Create `vars/conflict.yml`:

```yaml
---
app_env: "from_vars_files"
```

Modify `lab.yml`:

```yaml
---
- name: Demo conflict vars
  hosts: web1.lab
  vars:
    app_env: "from_play_vars"
  vars_files:
    - vars/conflict.yml
  tasks:
    - name: Quelle valeur gagne ?
      ansible.builtin.debug:
        var: app_env
```

**Before running**, **guess**: which wins, `from_play_vars` or `from_vars_files`?

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml
```

🔍 **Observation**: `from_vars_files` wins, and that is the **good surprise** of
this lab. In Ansible precedence, **`vars_files:` (level 14)** beats **the play's
`vars:` (level 12)**. Intuition says the opposite: `vars:` is written in the
play, right in front of you, so it should take priority. But level alone
decides, and the loaded file is higher.

**The common pitfall is therefore quite real, it simply goes the other way**: it
is not your `vars_files:` that is ignored, it is your `vars:`. When a play value
"does not take", look for a `vars_files:` before blaming Ansible.

**Now run with `--extra-vars`**:

```bash
ansible-playbook labs/ecrire-code/variables-base/lab.yml \
  --extra-vars "app_env=from_extra_vars"
```

🔍 **Observation**: `from_extra_vars` wins. **Level 22 (`--extra-vars`)** beats
everything.

This is exactly the topic of **lab 15 (precedence-variables)**, which covers the
22 levels in detail.

## 🔍 Observations to note

- **`vars:`** in the play = play scope, medium priority (level 12).
- **`vars_files:`** = same but in an external file (level 14, just **above**:
  the file **beats** the play, against all intuition).
- **`--extra-vars`** = absolute priority (level 22), overrides everything.
- **Strict YAML**: `yes/no` interpreted as booleans: use `true/false`.
- **Numeric strings** (IDs, version numbers): **always** in quotes.
- **`type_debug`** is the #1 diagnostic tool when "my variable is weird".

## 🤔 Reflection questions

1. You want an operator to be able to force `app_env=prod` during an emergency
   run without touching the code. Which approach: modify `vars:`, add a
   `vars_files:`, or use `--extra-vars`? Why?

2. A colleague sets `app_port: 8080` (no quotes) then uses this variable in a
   `curl http://localhost:{{ app_port }}/health` command. No problem. But on
   `app_id: 0042`, they read `42` instead of `0042` in their template. What is
   the difference and how to avoid it?

3. Why does `vars_files:` (level 14) beat the play's `vars:` (level 12), when one
   could imagine the opposite (the `vars:` is written in the play, so "closer")?
   Hint: which of the two carries an **operational decision**, and which carries
   a **default**?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`include_vars:`**: load vars **dynamically** at runtime (based on a condition,
  based on a detected OS). Different from `vars_files:` which is static, and
  stronger than it (level 18 versus 14).
- **`set_fact:`**: create a variable **on the managed node** during the play
  (level 19, beats the play vars like vars_files does). See lab 16.
- **`lookup('env', 'VAR')`**: read an environment variable from the control node.
  See lab 17 (lookups).
- **`ansible_<env>.yml` pattern**: one vars file per environment, loaded via
  `vars_files: - "vars/{{ env }}.yml"` with `env` passed via `--extra-vars`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/variables-base/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/variables-base/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/variables-base/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
