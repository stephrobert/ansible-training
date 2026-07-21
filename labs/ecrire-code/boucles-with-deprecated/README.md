# Lab 22 — Legacy `with_*` loops (to migrate to `loop:`)

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

🔗 [**Legacy Ansible loops: with_items, with_dict, migration to loop:**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-with-deprecated/)

Before Ansible 2.5, you used `with_items:`, `with_dict:`, `with_subelements:`,
`with_fileglob:`, `with_nested:`, etc. Since 2.5, **`loop:`** combined with **Jinja2
filters** (`dict2items`, `subelements`, `product`) covers all cases. The `with_*`
**still work** but are considered **legacy** by Ansible and the
RHCE 2026. This lab shows the **equivalences** to migrate existing code.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Recognize** the main forms `with_items`, `with_dict`, `with_subelements`,
   `with_fileglob`, `with_nested`.
2. **Migrate** each form to its `loop:` + Jinja2 filter equivalent.
3. **Use** `ansible-lint --fix` to automate the migration on existing code.
4. **Diagnose** the rare cases where the migration changes the semantics.
5. **Apply** the mapping table to a provided legacy code.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible db1.lab -m ping
ansible db1.lab -b -m shell -a "rm -f /tmp/withloop-*.txt /tmp/legacy-*.txt"
```

## 📚 Exercise 1 — `with_items` → `loop:` (the simplest)

```yaml
---
- name: Demo migration with_items
  hosts: db1.lab
  become: true
  tasks:
    - name: Forme legacy with_items
      ansible.builtin.copy:
        dest: "/tmp/legacy-{{ item }}.txt"
        content: "{{ item }}\n"
        mode: "0644"
      with_items: [pomme, banane, cerise]

    - name: Forme moderne loop
      ansible.builtin.copy:
        dest: "/tmp/loop-{{ item }}.txt"
        content: "{{ item }}\n"
        mode: "0644"
      loop: [pomme, banane, cerise]
```

**Run it**:

```bash
ansible-playbook labs/ecrire-code/boucles-with-deprecated/lab.yml
```

🔍 **Observation**: the **two forms** produce **the same files**.
Strictly equivalent behavior. The difference is purely syntactic.

## 📚 Exercise 2 — `with_dict` → `loop: + dict2items`

```yaml
- name: with_dict legacy
  ansible.builtin.copy:
    dest: "/tmp/legacy-port-{{ item.key }}.txt"
    content: "{{ item.key }} -> {{ item.value }}\n"
  with_dict:
    nginx: 80
    redis: 6379

- name: loop + dict2items moderne
  ansible.builtin.copy:
    dest: "/tmp/loop-port-{{ item.key }}.txt"
    content: "{{ item.key }} -> {{ item.value }}\n"
  loop: "{{ {'nginx': 80, 'redis': 6379} | dict2items }}"
```

🔍 **Observation**: `with_dict:` consumes a **dict directly**; `loop:` wants
a **list** so you go through `dict2items`, which produces
`[{key: nginx, value: 80}, ...]`. Identical output.

## 📚 Exercise 3 — `with_fileglob` → `loop: + query('fileglob')`

```yaml
- name: with_fileglob legacy
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "/tmp/legacy-glob-{{ item | basename }}"
  with_fileglob:
    - "files/*.conf"

- name: loop + query fileglob moderne
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "/tmp/loop-glob-{{ item | basename }}"
  loop: "{{ query('fileglob', 'files/*.conf') }}"
```

🔍 **Observation**: `with_fileglob:` is replaced by **`query('fileglob', ...)`**
which returns a list of paths. **`query`** is preferred over **`lookup`** here because
it **always returns a list** (even an empty one), ideal for `loop:`.

## 📚 Exercise 4 — `with_subelements` → `loop: + subelements`

```yaml
- name: Demo subelements
  vars:
    users:
      - name: alice
        ssh_keys:
          - "ssh-ed25519 AAAA1 alice-laptop"
          - "ssh-ed25519 AAAA2 alice-server"
      - name: bob
        ssh_keys:
          - "ssh-ed25519 BBBB1 bob-laptop"
  tasks:
    - name: with_subelements legacy
      ansible.builtin.debug:
        msg: "{{ item.0.name }} a la cle {{ item.1 }}"
      with_subelements:
        - "{{ users }}"
        - ssh_keys

    - name: loop + subelements moderne
      ansible.builtin.debug:
        msg: "{{ item.0.name }} a la cle {{ item.1 }}"
      loop: "{{ users | subelements('ssh_keys') }}"
```

🔍 **Observation**: `subelements` produces a **list of pairs `(parent, child)`**:

```
[
  ({name: alice, ssh_keys: [...]}, "ssh-ed25519 AAAA1 alice-laptop"),
  ({name: alice, ssh_keys: [...]}, "ssh-ed25519 AAAA2 alice-server"),
  ({name: bob, ssh_keys: [...]}, "ssh-ed25519 BBBB1 bob-laptop"),
]
```

Essential pattern for: **users + their SSH keys**, **services + their ports**,
**files + their templates**.

## 📚 Exercise 5 — `with_nested` → `loop: + product | list`

```yaml
- name: with_nested legacy
  ansible.builtin.debug:
    msg: "{{ item.0 }} et {{ item.1 }}"
  with_nested:
    - [a, b]
    - [1, 2]
  # Iterations : (a,1), (a,2), (b,1), (b,2)

- name: loop + product moderne
  ansible.builtin.debug:
    msg: "{{ item.0 }} et {{ item.1 }}"
  loop: "{{ ['a', 'b'] | product([1, 2]) | list }}"
```

🔍 **Observation**: `product` (Jinja2 filter) produces the **cartesian product**:
all the combinations. Handy for: **users × hosts**, **services × environments**.

## 📚 Exercise 6 — Automatic migration with `ansible-lint`

On existing legacy code, **`ansible-lint --fix`** can automatically migrate
most of the `with_*`.

```bash
# Reperer les with_* dans le repo
grep -rn "with_items\|with_dict\|with_fileglob\|with_subelements\|with_nested" labs/

# Tester sans modifier
ansible-lint labs/ecrire-code/boucles-with-deprecated/lab.yml --offline

# Migration automatique (modifie le fichier)
ansible-lint --fix labs/ecrire-code/boucles-with-deprecated/lab.yml
```

🔍 **Observation**: `ansible-lint --fix` detects the **`use-loop`** rule and offers
the migration. On simple cases (`with_items`, `with_dict`), the migration is
exact. On `with_subelements` or `with_nested`, the migration may require a
human review.

**Always**:

- **Backup** before `--fix` (intermediate git commit).
- **Tests** afterwards to check the semantic equivalence.

## 📚 Exercise 7 — The trap: `with_random_choice` has no direct equivalent

`with_random_choice:` returns **one** random element of a list, **not** an
iteration over the list.

```yaml
# Legacy : retourne UN element aleatoire
- name: with_random_choice legacy
  ansible.builtin.debug:
    msg: "Item : {{ item }}"
  with_random_choice: [a, b, c, d]
  # Itere une seule fois sur un element au hasard

# Moderne : utiliser le filtre random + boucle a 1 element
- name: loop avec random
  ansible.builtin.debug:
    msg: "Item : {{ item }}"
  loop: "{{ ['a', 'b', 'c', 'd'] | random | list }}"
```

🔍 **Observation**: the migration requires understanding the **intent** of the `with_random_choice` (1 iteration over 1 random element): there is no
syntactically direct equivalent, so you wrap it in a list.

## 🔍 Observations to note

- **`loop:` replaces all the `with_*`** since Ansible 2.5.
- **`with_dict:`** → **`loop: + dict2items`**.
- **`with_fileglob:`** → **`loop: + query('fileglob', ...)`**.
- **`with_subelements:`** → **`loop: + subelements`** (Jinja2 filter).
- **`with_nested:`** → **`loop: + product | list`**.
- **`ansible-lint --fix`** automates the migration on simple cases.
- **No direct migration** for `with_random_choice`, `with_first_found`, etc.

## 🤔 Reflection questions

1. Why did Ansible **not deprecate** the `with_*` (just "legacy")? What
   would be the cost of a plain and simple removal?

2. The form `with_items: "{{ packages }}"` (with interpolation) has worked for a
   long time. The form `loop: "{{ packages }}"` too. What is the **technical
   difference** between the two? (hint: see the `lookup` plugin concept).

3. You pick up a playbook with 50 `with_*`. You run `ansible-lint --fix`.
   What are the **3 checks to do** before committing?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Performance**: no measurable difference between `with_*` and `loop:`.
  The "loop is faster" argument is false. The real difference is semantic
  and standardization.
- **Legacy code migration**: combine `ansible-lint --fix` + functional tests
  + Molecule. For a repo of 100 roles, plan 1-2 days of validation.
- **`use_loop` rule**: ansible-lint rule that detects the `with_*` (except
  `with_first_found` and `with_random_choice`, which are kept for their
  particular semantics).
- **RHCE 2026**: prefer `loop:` on all new code. The `with_*` are **not
  penalized** on the exam but the **expected style** is `loop:`.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint de votre fichier de lab (tutoriel guidé)
ansible-lint labs/ecrire-code/boucles-with-deprecated/lab.yml

# Lint de votre solution challenge
ansible-lint labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml

# Profil production (le plus strict — cible RHCE 2026)
ansible-lint --profile production labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
