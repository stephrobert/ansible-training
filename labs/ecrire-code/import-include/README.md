# Lab 30a — Import vs Include (`import_tasks`, `include_tasks`, `import_role`, `include_role`, `import_playbook`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**Import vs Include: the 5 Ansible directives**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/playbooks/import-include/)

Ansible offers **5 directives** to split a playbook into reusable files:

- **`import_tasks`** / **`include_tasks`**: include a tasks file.
- **`import_role`** / **`include_role`**: include a role.
- **`import_playbook`**: include another playbook (at the plays level).

The distinction **`import_*` (static) vs `include_*` (dynamic)** is **fundamental** and **tested on the EX294**: they do **not behave the same** regarding **tags**, **conditions**, **runtime variables**, **handlers**, and **`--list-tasks`**. Confusing the two silently breaks your playbooks.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Distinguish** `import_*` (static, parsed at start) vs `include_*` (dynamic, parsed at runtime).
2. **Choose** the right directive depending on the case (loop? conditional? runtime variables?).
3. **Split** a playbook with `import_tasks` for readability.
4. **Call** a role dynamically with `include_role` (useful for `loop:`).
5. **Orchestrate** several plays with `import_playbook`.
6. **Understand** how `tags:` and `when:` behave differently depending on import vs include.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
ansible db1.lab -b -m ansible.builtin.shell -a "rm -f /tmp/lab30a-*" 2>&1 | tail -2
```

## ⚙️ Target tree

```text
labs/ecrire-code/import-include/
├── README.md                       ← this file (guided tutorial)
└── challenge/
    ├── README.md                   ← challenge instructions
    └── tests/
        └── test_import_include.py
```

The learner writes `lab.yml` + the `tasks/*.yml` files + `challenge/solution.yml` themselves.

## 📚 Exercise 1 — `import_tasks` static vs `include_tasks` dynamic

Create 2 tasks files:

`tasks/install.yml`:

```yaml
---
- name: Marker install
  ansible.builtin.copy:
    dest: "{{ marker_path }}"
    content: "step: install\n"
    mode: "0644"
```

`tasks/configure.yml`:

```yaml
---
- name: Marker configure
  ansible.builtin.copy:
    dest: "{{ marker_path }}"
    content: "step: configure\n"
    mode: "0644"
```

In `lab.yml`:

```yaml
---
- hosts: db1.lab
  become: true
  gather_facts: false
  vars:
    marker_path: /tmp/lab30a-marker.txt
  tasks:
    - name: Static — import_tasks (parsé au start)
      ansible.builtin.import_tasks: tasks/install.yml

    - name: Dynamic — include_tasks (parsé au runtime)
      ansible.builtin.include_tasks: tasks/configure.yml
```

🔍 **Observation**: to the eye, **nothing distinguishes** the 2 directives at run time. But what changes is **internal**: `import_*` is **resolved at startup** (before execution), `include_*` at **runtime** (when the task is reached).

## 📚 Exercise 2 — The REAL difference: runtime variables

Case where the difference is obvious: **a variable defined at runtime** in a loop.

```yaml
- hosts: db1.lab
  gather_facts: false
  tasks:
    - name: Include dynamic dans une loop (FONCTIONNE)
      ansible.builtin.include_tasks: tasks/install.yml
      vars:
        marker_path: "/tmp/lab30a-loop-{{ item }}.txt"
      loop: [1, 2, 3]

    # - name: Import static dans une loop (NE FONCTIONNE PAS)
    #   ansible.builtin.import_tasks: tasks/install.yml   ← loop KO
    #   vars:
    #     marker_path: "..."
    #   loop: [1, 2, 3]
```

🔍 **Crucial observation**: `import_*` **does not accept `loop:`** because it is resolved at startup (the loop variable does not exist yet). `include_*` accepts `loop:`. **Rule**: to loop over a tasks file, use **`include_tasks`**.

## 📚 Exercise 3 — Difference on `tags:`

```yaml
- hosts: db1.lab
  tasks:
    - name: Import static — les tags se PROPAGENT aux tâches incluses
      ansible.builtin.import_tasks: tasks/install.yml
      tags: [setup]

    - name: Include dynamic — les tags ne se propagent PAS
      ansible.builtin.include_tasks: tasks/configure.yml
      tags: [setup]
```

Run with `--tags setup`:

```bash
ansible-playbook lab.yml --tags setup
```

🔍 **Observation**:
- `import_tasks` propagates **`setup`** to **all** the tasks of the imported file. `--tags setup` runs them.
- `include_tasks` **does not apply the tag** to the tasks **internal** to the included file. For them to be tagged, you must tag **each task** in `configure.yml`. A frequent source of bugs.

## 📚 Exercise 4 — Difference on the `when:` conditional

```yaml
- hosts: db1.lab
  tasks:
    - name: Import — when s'applique à TOUTES les tâches importées
      ansible.builtin.import_tasks: tasks/install.yml
      when: inventory_hostname == "db1.lab"

    - name: Include — when s'évalue UNE FOIS sur le include lui-même
      ansible.builtin.include_tasks: tasks/configure.yml
      when: inventory_hostname == "db1.lab"
```

🔍 **Observation**: **subtly different** semantics. `import_*` propagates the `when:` to each task → per-task evaluation. `include_*` evaluates the `when:` **only once** at the moment of the include (before running the content).

## 📚 Exercise 5 — `import_role` vs `include_role`

```yaml
- hosts: db1.lab
  tasks:
    - name: Import role static (équivalent au mot-clé `roles:` du play)
      ansible.builtin.import_role:
        name: my_role

    - name: Include role dynamic (utilisable dans une loop, conditionnel runtime)
      ansible.builtin.include_role:
        name: my_role
      loop: [1, 2, 3]                       # ← loop OK with include_role
```

🔍 **Observation**: `import_role` ≈ the classic play's `roles:`. `include_role` lets you **loop over a role** or apply a role **conditionally at runtime**, a rare but powerful use for dynamic patterns.

## 📚 Exercise 6 — `import_playbook` to orchestrate

A single orchestration file `site.yml` that chains several playbooks:

```yaml
---
# site.yml: orchestrator
- ansible.builtin.import_playbook: playbooks/install_db.yml
- ansible.builtin.import_playbook: playbooks/install_web.yml
- ansible.builtin.import_playbook: playbooks/configure_app.yml
```

🔍 **Observation**: **`import_playbook`** is **static only** (there is no `include_playbook`). Use it at the **plays level** (not in `tasks:`). Standard pattern to split a large deployment into reusable sub-playbooks.

## 📚 Exercise 7 — Decision table

| Use case | Directive |
|-------------|-----------|
| Split a playbook into `tasks/*.yml` files (no loop) | **`import_tasks`** (static, faster, supports `--list-tasks`) |
| Loop over a tasks file (`loop: [...]`) | **`include_tasks`** (only) |
| Tag a whole block of included tasks | **`import_tasks` + `tags:`** (propagates automatically) |
| Call a role classically | **`import_role`** or the play's `roles:` directive |
| Loop over a role | **`include_role`** + `loop:` |
| Orchestrate several plays | **`import_playbook`** (only) |
| Runtime variable not yet known at start | **`include_*`** (any) |

## 🔍 Observations to note

- **`import_*`** = **static**, parsed at startup. Faster. Tags + when propagated.
- **`include_*`** = **dynamic**, parsed at runtime. Supports `loop:`. Tags + when **not propagated**.
- **`import_playbook`** exists, **`include_playbook` does NOT exist**.
- **Loop over tasks/roles** → **`include_*`** mandatory.
- **`--list-tasks`** only sees the **imported** tasks (static), not the included ones (dynamic).

## 🤔 Reflection questions

1. Why is `import_*` **faster at start** than `include_*`?
2. What does `ansible-playbook --list-tasks` return for an `include_tasks`?
3. If you tag `import_tasks: ... tags: [setup]`, do you also need to tag the tasks **inside** the imported file?
4. Which directive should you choose to **import an entire playbook**: `import_playbook` or `include_playbook`?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): combine `import_tasks` (static) + `include_tasks` (with a loop) + a separate task, dropping the marker files that prove each mechanism ran.

## 💡 Going further

- **Lab 11**: `delegate_to`, which can be used at the task or block level.
- **Lab 23**: `block/rescue/always`, an alternative to group tasks.
- **`apply:`** on `include_tasks`: applies tags / become / when to all the **internal** tasks. Example: `include_tasks: ... apply: { tags: [setup] }`.

## 🔍 Linting with `ansible-lint`

```bash
ansible-lint labs/ecrire-code/import-include/lab.yml
ansible-lint --profile production labs/ecrire-code/import-include/challenge/solution.yml
```

> 💡 **Tip**: `ansible-lint` detects the **non-FQCN** module (`include_tasks:` instead of `ansible.builtin.include_tasks:`) with the `fqcn-builtins` rule. Always use the full FQCN.
