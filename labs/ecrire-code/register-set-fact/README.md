# Lab 16 — `register:` and `set_fact:` (capturing and creating variables)

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

🔗 [**Ansible register and set_fact: capture, lifetime, cacheable**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/register-set-fact/)

`register: var` captures the result of a module into a variable (`rc`, `stdout`,
`stderr`, `changed`, `failed`, plus module-specific fields). `set_fact:`
creates or recomputes a variable at runtime: level 19 in the precedence (so it beats
the play's `vars:`). These two mechanisms are the **basis of the "task → decision" pattern**
in Ansible: run, observe, act depending on the result.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Capture** a module's output with `register:` and explore its structure.
2. **Reuse** a captured field in a following task (`when:`, `loop:`).
3. **Create** a variable at runtime via `set_fact:` from filtering logic.
4. **Persist** a fact via `cacheable: true` for later runs.
5. **Distinguish** the scope and lifetime of `register:` vs `set_fact:`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/register-*.txt /tmp/setfact-*.txt"
```

## 📚 Exercise 1 — `register:` simple on `command:`

Create `lab.yml`:

```yaml
---
- name: Demo register simple
  hosts: db1.lab
  become: true
  tasks:
    - name: Capturer la version d openssl
      ansible.builtin.command: openssl version
      register: ssl_result
      changed_when: false

    - name: Inspecter la structure complete de la variable register
      ansible.builtin.debug:
        var: ssl_result

    - name: Utiliser uniquement le stdout
      ansible.builtin.debug:
        msg: "openssl version : {{ ssl_result.stdout }}"
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/register-set-fact/lab.yml
```

🔍 **Observation**: the first `debug: var: ssl_result` shows **the whole structure**
returned by the module:

```yaml
ssl_result:
  cmd: ['openssl', 'version']
  rc: 0
  stdout: "OpenSSL 3.x.x ..."
  stdout_lines: ['OpenSSL 3.x.x ...']
  stderr: ""
  start: "..."
  end: "..."
  delta: "0:00:00.012345"
  failed: false
  changed: false
```

**Most useful fields**:

- **`rc`**: the process return code (0 = success).
- **`stdout`** / **`stdout_lines`**: raw output / list of lines.
- **`failed`** / **`changed`**: the task's statuses.
- **`delta`**: execution duration.

## 📚 Exercise 2 — Condition on `register:`

```yaml
- name: Tester si /etc/passwd existe
  ansible.builtin.stat:
    path: /etc/passwd
  register: passwd_stat

- name: Action si le fichier existe et est non vide
  ansible.builtin.copy:
    content: "passwd existe, taille {{ passwd_stat.stat.size }} octets\n"
    dest: /tmp/register-passwd-stat.txt
    mode: "0644"
  when: passwd_stat.stat.exists and passwd_stat.stat.size > 0
```

🔍 **Observation**: `stat:` is the **diagnostic** module par excellence: used
in tandem with `register:` + `when:`, it lets you code robust **conditional
branches**.

**Common fields of `stat:`**:

- `passwd_stat.stat.exists` (bool)
- `passwd_stat.stat.isfile` / `passwd_stat.stat.isdir` / `passwd_stat.stat.islnk`
- `passwd_stat.stat.size` (bytes)
- `passwd_stat.stat.mode` (octal string `'0644'`)
- `passwd_stat.stat.checksum` (SHA1 of the content, if a file)

## 📚 Exercise 3 — `register:` + `loop:` (multi-iteration capture)

```yaml
- name: Tester plusieurs services
  ansible.builtin.systemd_service:
    name: "{{ item }}"
  register: services_status
  loop:
    - sshd
    - chronyd
    - rsyslog
  changed_when: false
  failed_when: false

- name: Inspecter la structure (liste de results)
  ansible.builtin.debug:
    var: services_status.results | map(attribute='name') | list

- name: Extraire ceux qui sont active
  ansible.builtin.debug:
    msg: "Active : {{ services_status.results | selectattr('status.ActiveState', 'equalto', 'active') | map(attribute='name') | list }}"
```

🔍 **Observation**: with `loop:`, `register:` captures **a list** under `.results`.
Each element contains the iteration's result + the value of `item`. To
extract a subset, the `selectattr` filter is the natural tool.

## 📚 Exercise 4 — `set_fact:` (creating a variable at runtime)

`set_fact` is useful to **compute** a variable from several sources.

```yaml
- name: Calculer le mode de deploy selon l environnement
  ansible.builtin.set_fact:
    deploy_mode: >-
      {% if ansible_distribution_major_version | int >= 9 %}
      modern
      {% else %}
      legacy
      {% endif %}

- name: Calculer le label en concatenant
  ansible.builtin.set_fact:
    deploy_label: "{{ inventory_hostname }}-{{ ansible_date_time.epoch }}"

- name: Utiliser les facts crees
  ansible.builtin.copy:
    content: |
      Mode : {{ deploy_mode | trim }}
      Label : {{ deploy_label }}
    dest: /tmp/setfact-marker.txt
    mode: "0644"
```

🔍 **Observation**: `set_fact:` creates a variable **immediately available** in
the following tasks of the same play. Major difference with `vars:`: the value can
be **computed** (concatenation, condition, filters).

**Precedence level**: 19. `set_fact` (and `registered` variables, same
level) beats the play's `vars:` (12), `vars_files:` (14), `include_vars` (18) and all
the group_vars/host_vars. Handy to **force** a computed value. Only the
role params (20), the include params (21) and `--extra-vars` (22) override it.

## 📚 Exercise 5 — `cacheable: true` (persisting across runs)

If `fact_caching = jsonfile` is configured in `ansible.cfg`, you can **persist**
a fact created by `set_fact`:

```yaml
- name: Set fact persistant
  ansible.builtin.set_fact:
    last_deploy_label: "{{ inventory_hostname }}-{{ ansible_date_time.epoch }}"
    cacheable: true
```

**Run the playbook once**, then **a second playbook** that only does:

```yaml
- name: Lire le fact precedent
  ansible.builtin.debug:
    var: last_deploy_label
```

🔍 **Observation**: if `cacheable: true` was present on the first run and fact
caching enabled, the value **survives** into the second run, **without regathering facts**.

**Inspect the cache**:

```bash
ls .ansible_facts/  # Defined in ansible.cfg: fact_caching_connection
cat .ansible_facts/s1_db1.lab | python3 -m json.tool | grep last_deploy
```

## 📚 Exercise 6 — The trap: `register:` in a loop, direct access

Classic mistake: trying to access `myreg.stdout` after a loop, forgetting
that `register` returns a **list** under `.results`.

```yaml
- name: Boucle qui capture
  ansible.builtin.command: "echo {{ item }}"
  loop: [a, b, c]
  register: outputs
  changed_when: false

- name: Erreur typique (ne fait que prendre la derniere)
  ansible.builtin.debug:
    msg: "stdout : {{ outputs.stdout | default('absent') }}"

- name: Forme correcte
  ansible.builtin.debug:
    msg: "stdouts : {{ outputs.results | map(attribute='stdout') | list }}"
```

🔍 **Observation**: `outputs.stdout` is `absent` (the key does not exist at the
root level when there is a `loop:`). The correct form goes through **`.results`** + `map`.

## 🔍 Observations to note

- **`register:`** captures the result of **a module** under a variable (rc, stdout, stderr, custom).
- **With `loop:`**, `register:` returns a **list** under `.results`.
- **`set_fact:`** creates a variable at runtime: level 19 in the precedence
  (not to be confused with `include_vars`, which is 18, just below).
- **`cacheable: true`** on `set_fact` persists the value if `fact_caching` is configured.
- **`stat:` + `register:` + `when:`** = the trio of robust **conditional logic**.
- **`changed_when: false`** on a read-only `command:` so it does not report `changed`.

## 🤔 Reflection questions

1. You run 5 `dnf install` commands in a `loop:`, and you want to **report
   only the ones that changed**. How do you write the filter on the `register`?

2. Why is `set_fact:` **level 19** (higher priority than the play's `vars:` at 12,
   and than `vars_files:` at 14)? What use case justifies this precedence?

3. You capture the output of a `command:` that returns a multi-line JSON. How do you
   parse this JSON into a usable Ansible variable? (hint: `from_json` filter).

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`changed_when:`** + **`failed_when:`**: redefine a task's state depending
  on the output. See lab 23.
- **`from_json`** / **`from_yaml`**: parse a text output into a native structure for
  Jinja2 manipulation.
- **`ansible_facts.<key>`**: the official namespace for facts. Prefer
  `ansible_facts.distribution` to `ansible_distribution` in new playbooks
  (config `inject_facts_as_vars = false` eventually).
- **The `register: r` + `r.stdout | trim` pattern**: the trailing `\n` of shell commands
  is a recurring trap that breaks string comparisons.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/register-set-fact/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/register-set-fact/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/register-set-fact/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
