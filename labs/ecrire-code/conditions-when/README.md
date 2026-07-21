# Lab 20 — `when:` conditions

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

🔗 [**Ansible conditions: when, operators, multi-conditions**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/conditions-when/)

`when:` filters the execution of a task based on a **Jinja2 boolean expression**.
Without a condition, the task runs on all the targeted hosts. With `when:`, it only
runs on those that satisfy the expression. Conditions are the **number 1 tool
of Ansible programming**: multi-OS, progressive deployment, conditional
branches. Peculiarity: no `{{ }}` in `when:`, the expression is
**already** Jinja2.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Condition** a task on a fact (`ansible_distribution`, OS version).
2. **Combine** several conditions with `and`, `or`, parentheses.
3. **Test** the definition of a variable (`is defined`, `is not defined`).
4. **Use** the Jinja2 tests (`is mapping`, `is sequence`, `is regex`).
5. **Diagnose** a `when:` that matches wrong (often a bool vs string type).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ping
ansible all -b -m shell -a "rm -f /tmp/when-*.txt"
```

## 📚 Exercise 1 — Simple condition on a fact

Create `lab.yml`:

```yaml
---
- name: Demo when sur fact OS
  hosts: all
  become: true
  gather_facts: true
  tasks:
    - name: Tache RHEL/AlmaLinux/Rocky uniquement
      ansible.builtin.copy:
        content: "Famille redhat\n"
        dest: /tmp/when-redhat.txt
        mode: "0644"
      when: ansible_os_family == "RedHat"

    - name: Tache version major >= 9
      ansible.builtin.copy:
        content: "Version majeur {{ ansible_distribution_major_version }}\n"
        dest: /tmp/when-version.txt
        mode: "0644"
      when: ansible_distribution_major_version | int >= 9
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/conditions-when/lab.yml
```

🔍 **Observation**: on AlmaLinux 9, the **2 tasks run**. The files
are created on web1, web2, db1. If you had a Debian in the lab, **neither** of the
two tasks would run on it.

**No `{{ }}` in `when:`**:

```yaml
when: ansible_os_family == "RedHat"     # ✅
when: "{{ ansible_os_family == 'RedHat' }}"   # ❌ Ansible warning
```

## 📚 Exercise 2 — Combine with `and`, `or`

```yaml
- name: AlmaLinux ET version 10
  ansible.builtin.copy:
    content: "AlmaLinux 9\n"
    dest: /tmp/when-and.txt
    mode: "0644"
  when:
    - ansible_distribution == "AlmaLinux"
    - ansible_distribution_major_version | int == 10

- name: RHEL OU AlmaLinux (operator or explicite)
  ansible.builtin.copy:
    content: "RHEL ou AlmaLinux\n"
    dest: /tmp/when-or.txt
    mode: "0644"
  when: ansible_distribution == "RedHat" or ansible_distribution == "AlmaLinux"
```

🔍 **Observation**: the **list under `when:`** (YAML form with dashes) is an **implicit
AND** between the conditions. To do an `OR`, you must write the operator
explicitly on a single line.

**Parentheses for priority**:

```yaml
when: (ansible_os_family == "RedHat" and ansible_distribution_major_version | int >= 9) or
      (ansible_os_family == "Debian" and ansible_distribution_major_version | int >= 11)
```

## 📚 Exercise 3 — Test the definition of a variable

```yaml
- name: Tache si optional_var defini
  ansible.builtin.copy:
    content: "Variable optional_var = {{ optional_var }}\n"
    dest: /tmp/when-defined.txt
    mode: "0644"
  when: optional_var is defined

- name: Tache si optional_var absent
  ansible.builtin.copy:
    content: "optional_var n est pas defini\n"
    dest: /tmp/when-undefined.txt
    mode: "0644"
  when: optional_var is not defined
```

**Run it first WITHOUT the variable**:

```bash
ansible-playbook labs/ecrire-code/conditions-when/lab.yml
```

🔍 **Observation**: only the second task runs (`/tmp/when-undefined.txt`
created, `/tmp/when-defined.txt` skipped).

**Rerun WITH the variable**:

```bash
ansible-playbook labs/ecrire-code/conditions-when/lab.yml \
  --extra-vars "optional_var=hello"
```

🔍 **Observation**: it is the opposite, the `when-defined.txt` file is created.

## 📚 Exercise 4 — Type tests (`is mapping`, `is sequence`)

```yaml
- name: Tester le type de variable
  vars:
    config_dict: {host: db1, port: 5432}
    config_list: [a, b, c]
    config_string: "hello"
  block:
    - name: Test mapping (dict)
      ansible.builtin.debug:
        msg: "config_dict est un dict"
      when: config_dict is mapping

    - name: Test sequence (list)
      ansible.builtin.debug:
        msg: "config_list est une liste"
      when: config_list is sequence and config_list is not string

    - name: Test string
      ansible.builtin.debug:
        msg: "config_string est une string"
      when: config_string is string
```

🔍 **Observation**: useful tests for **polymorphic tasks** that accept a
string OR a list, for example. Combined with `default`, you can write:

```yaml
loop: "{{ packages if packages is sequence else [packages] }}"
```

This pattern accepts `packages: nginx` (single string) **or** `packages: [nginx, redis]`
(list).

## 📚 Exercise 5 — Condition a loop (`when:` on the item)

```yaml
- name: Creer uniquement les services enabled
  ansible.builtin.debug:
    msg: "Service {{ item.name }} sur port {{ item.port }}"
  loop:
    - { name: nginx, port: 80, enabled: true }
    - { name: redis, port: 6379, enabled: false }
    - { name: postgresql, port: 5432, enabled: true }
  when: item.enabled
```

🔍 **Observation**: `when:` can reference **`item`** in a loop. The task
skips redis (`enabled: false`), it is `skipped`, not `changed`.

**Combination with a fact**:

```yaml
loop: "{{ services }}"
when:
  - item.enabled
  - ansible_distribution == "AlmaLinux"
  - item.os_compatible | default(['all']) | contains(ansible_distribution)
```

## 📚 Exercise 6 — The trap: bool vs string type

Surprising case: `when: app_enabled` can **always be true** even when you expect
"false".

```yaml
- name: Demo piege type
  vars:
    app_enabled_str: "false"   # string "false"
    app_enabled_bool: false    # bool false
  block:
    - name: Tache avec string
      ansible.builtin.debug:
        msg: "Tache avec string false"
      when: app_enabled_str
      # ATTENTION : tourne ! Une string non vide est truthy en Python

    - name: Tache avec bool
      ansible.builtin.debug:
        msg: "Tache avec bool false"
      when: app_enabled_bool
      # OK : ne tourne pas
```

🔍 **Observation**: `when: "false"` (string) → **truthy** (any non-empty string
is truthy). `when: false` (bool) → falsy.

**Source of the trap**: `--extra-vars "app_enabled=false"` passes a **string** (the CLI
does no YAML typing). The real value is `"false"`, not `False`.

**Solution**: force the bool with the `bool` filter:

```yaml
when: app_enabled | bool
```

`| bool` recognizes `'true'`, `'yes'`, `'1'` as true and `'false'`, `'no'`, `'0'`
as false.

## 🔍 Observations to note

- **`when:`** = Jinja2 expression **without `{{ }}`**.
- **List under `when:`** = implicit AND between the elements.
- **`is defined` / `is not defined`** = test the existence of a variable.
- **`is mapping` / `is sequence` / `is string`** = test the type.
- **`when: var | bool`** = force the conversion to bool (avoids the string truthy trap).
- **`when:` in a `loop:`** = filter by item, not by task.

## 🤔 Reflection questions

1. You have a playbook that must run on **RHEL 9+** **OR** **Debian 11+**.
   How do you write the `when:` (combination of `and` / `or` / parentheses)?

2. `when: my_dict.field is defined` returns **true** even when `my_dict.field`
   is `null`. What is the difference between "defined" and "not null"?

3. Why can `--extra-vars "app_enabled=false"` make a task
   conditioned by `when: app_enabled` **run**? What is the clean mitigation?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`when:` on a block**: applies the condition to all the tasks of the block.
  More DRY than repeating the same condition on 5 tasks.
- **`failed_when:` + `when:`**: combine to build a complex audit
  logic (ex: fail if a mandatory file is absent AND on RHEL 9+).
- **Custom tests** (`is regex`, `is search`): match a regex on a string.
  `when: ansible_kernel is search('5\\.14')`.
- **`vars_prompt:` + `when:` pattern**: condition on an interactive user
  answer (rare but useful for one-shot plays).

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/conditions-when/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/conditions-when/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/conditions-when/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
