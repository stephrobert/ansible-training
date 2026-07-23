# Lab 21 — `loop:` loops (`loop_control`, `dict2items`)

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

🔗 [**Ansible loops: loop, loop_control, dict2items**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-loop/)

`loop:` is the modern directive (Ansible 2.5+) to repeat a task over a **list**
or a **dict** (via `dict2items`). It replaces the old `with_items:`,
`with_dict:`, `with_*` forms (lab 21). `loop_control:` lets you adjust the display
(`label`), the pause (`pause`), the index (`index_var`), and the loop variable
(`loop_var`). It is the basis of any playbook that creates several resources:
users, packages, services, files.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Loop** over a simple list and a list of dicts.
2. **Use** `loop_control: label:` to make the console output readable.
3. **Loop** over a dict via `dict2items`.
4. **Retrieve** the index with `loop_control: index_var:`.
5. **Diagnose** a case where `item` is ambiguous (nested loop).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/loop-*.txt; userdel -rf alice 2>/dev/null; userdel -rf bob 2>/dev/null; userdel -rf charlie 2>/dev/null; true"
```

## 📚 Exercise 1 — Simple loop over a list of strings

Create `lab.yml`:

```yaml
---
- name: Demo loop simple
  hosts: db1.lab
  become: true
  vars:
    fruits: [pomme, banane, cerise]
  tasks:
    - name: Creer un fichier par fruit
      ansible.builtin.copy:
        content: "Fruit : {{ item }}\n"
        dest: "/tmp/loop-fruit-{{ item }}.txt"
        mode: "0644"
      loop: "{{ fruits }}"
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/boucles-loop/lab.yml
```

🔍 **Observation**: 3 iterations, 3 files created. The console output shows
`[item=pomme]`, `[item=banane]`, `[item=cerise]`: for this simple structure,
it is readable. On dicts, you will need `loop_control: label:`.

## 📚 Exercise 2 — List of dicts + `loop_control: label:`

```yaml
- name: Creer 3 users
  hosts: db1.lab
  become: true
  vars:
    users:
      - { name: alice, shell: /bin/bash, enabled: true }
      - { name: bob, shell: /bin/zsh, enabled: false }
      - { name: charlie, shell: /bin/bash, enabled: true }
  tasks:
    - name: Creer les users actifs
      ansible.builtin.user:
        name: "{{ item.name }}"
        shell: "{{ item.shell }}"
        state: present
      loop: "{{ users }}"
      loop_control:
        label: "{{ item.name }}"
      when: item.enabled
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/boucles-loop/lab.yml
```

🔍 **Observation**:

- **3 iterations**, **2 changed** (alice, charlie), **1 skipped** (bob, `enabled: false`).
- The output shows `[item=alice]` instead of `[item={'name': 'alice', 'shell': '/bin/bash', ...}]`.

**Without `loop_control: label:`** the output is unreadable:

```
[item={'name': 'alice', 'shell': '/bin/bash', 'enabled': True}]
[item={'name': 'bob', 'shell': '/bin/zsh', 'enabled': False}]
```

→ **Always** put a `label:` in loops over dicts.

## 📚 Exercise 3 — Loop over a dict with `dict2items`

`loop:` wants a **list**. To loop over a **dict**, you use the
`dict2items` filter which converts `{a: 1, b: 2}` into `[{key: a, value: 1}, {key: b, value: 2}]`.

```yaml
- name: Demo loop sur dict
  hosts: db1.lab
  become: true
  vars:
    ports:
      nginx: 80
      redis: 6379
      postgresql: 5432
  tasks:
    - name: Creer un fichier par service / port
      ansible.builtin.copy:
        content: "{{ item.key }} ecoute sur le port {{ item.value }}\n"
        dest: "/tmp/loop-port-{{ item.key }}.txt"
        mode: "0644"
      loop: "{{ ports | dict2items }}"
      loop_control:
        label: "{{ item.key }}={{ item.value }}"
```

🔍 **Observation**: `item.key` = `nginx/redis/postgresql`, `item.value` = `80/6379/5432`.
The `label:` shows `[item=nginx=80]`: readable.

## 📚 Exercise 4 — `index_var` and `pause`

```yaml
- name: Demo index_var et pause
  hosts: db1.lab
  become: true
  vars:
    items_list: [un, deux, trois, quatre, cinq]
  tasks:
    - name: Iteration avec index
      ansible.builtin.copy:
        content: "Item {{ idx }} : {{ item }}\n"
        dest: "/tmp/loop-indexed-{{ idx }}.txt"
        mode: "0644"
      loop: "{{ items_list }}"
      loop_control:
        label: "{{ idx }}/{{ items_list | length }}"
        index_var: idx
        pause: 1
```

🔍 **Observation**:

- **`index_var: idx`** = name of the index variable (by default, not exposed). Lets you
  generate unique names `loop-indexed-0.txt`, `loop-indexed-1.txt`, etc.
- **`pause: 1`** = wait of 1 second **between each iteration**. Useful for
  rate-limited API calls, or long operations to spread out.

## 📚 Exercise 5 — Nested loop and `loop_var`

When you have **two nested loops** (e.g.: a block in a loop that
itself contains a loop), `item` becomes ambiguous: you must rename it.

```yaml
- name: Demo boucles imbriquees
  hosts: db1.lab
  become: true
  vars:
    users:
      - { name: alice, files: [.bashrc, .vimrc] }
      - { name: bob, files: [.bashrc] }
  tasks:
    - name: Creer fichier marker pour chaque user/file combination
      block:
        - name: Inner loop sur les fichiers du user courant
          ansible.builtin.debug:
            msg: "User {{ user_item.name }}, file {{ file_item }}"
          loop: "{{ user_item.files }}"
          loop_control:
            loop_var: file_item
      loop: "{{ users }}"
      loop_control:
        loop_var: user_item
        label: "{{ user_item.name }}"
```

🔍 **Observation**: `loop_var: user_item` renames `item` of the outer loop to
`user_item`, and `loop_var: file_item` renames the inner loop to `file_item`.
Without these renamings, the inner loop would have overwritten the outer's `item`: a silent bug.

## 📚 Exercise 6 — The trap: `loop` with a string (not a list)

```yaml
- name: Piege loop sur string
  vars:
    not_a_list: "abc"
  ansible.builtin.debug:
    msg: "Item : {{ item }}"
  loop: "{{ not_a_list }}"
```

🔍 **Observation**: Ansible iterates **character by character**! Output:

```
[item=a]
[item=b]
[item=c]
```

A **string is iterable** in Python, but this is generally not what you want.

**Solutions**:

```yaml
# Forcer une liste a 1 element
loop: "{{ [not_a_list] }}"

# Ou tester si c est deja une liste
loop: "{{ not_a_list if not_a_list is sequence and not_a_list is not string else [not_a_list] }}"
```

## 🔍 Observations to note

- **`loop:`** replaces all the legacy `with_*` (since Ansible 2.5).
- **`loop_control: label:`** is **mandatory in practice** on loops over dicts.
- **`dict2items`** converts a dict into a `[{key, value}]` list to loop over.
- **`index_var:`** + **`pause:`** = useful options for pacing and identification.
- **`loop_var:`** is mandatory for nested loops.
- **`loop:` over a string** iterates character by character: a frequent trap.

## 🤔 Reflection questions

1. You want to create `/etc/myapp/conf.d/<name>.conf` files from a
   list of dicts `{name, content}`. How do you articulate `loop:`, `template:`,
   and `loop_control:`?

2. `loop:` accepts a string and iterates character by character. How do you **force**
   `loop:` to always treat its value as **a single iteration** (whether it is a
   string or a 1-element list)?

3. You loop over 100 packages with `package:` + `loop:`. It is slow. Why
   is `package: name: [...]` (without loop) much faster?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **`loop_control: extended: true`**: exposes `ansible_loop` with
  `index`, `index0`, `first`, `last`, `length`, `revindex`, `previtem`, `nextitem`.
  Very useful for conditional Jinja2 templates (last item without a comma, etc.).
- **`until:` + `retries:` + `delay:`**: retry of a task until a condition is
  satisfied. Different from `loop:` (which iterates over data).
- **Flatten pattern**: `loop: "{{ [list1, list2] | flatten }}"` to merge
  several lists into a single loop.
- **`subelements`**: loop over **sub-elements** of a list of dicts,
  equivalent of the SQL `JOIN`. See lab 21 (with-deprecated) for the migration from
  `with_subelements`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/boucles-loop/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/boucles-loop/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/boucles-loop/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
