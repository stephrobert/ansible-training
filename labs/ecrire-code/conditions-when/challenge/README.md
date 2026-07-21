# 🎯 Challenge — Targeted `when` conditions

## ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** lays down **3 conditional
files** and **does not lay down a 4th** (proof that a false `when` cleanly
skips the task).

| File to lay down | `when` condition | Expected content |
| --- | --- | --- |
| `/tmp/cond-redhat.txt` | `ansible_os_family == "RedHat"` | `famille=redhat` |
| `/tmp/cond-alma9.txt` | `AlmaLinux` AND version ≥ 9 | `os=AlmaLinux9` |
| `/tmp/cond-feature.txt` | `enable_feature` is defined AND truthy | `feature=enabled` |

| File to **NOT** lay down | `when` condition |
| --- | --- |
| `/tmp/cond-debian.txt` | `ansible_os_family == "Debian"` (false on AlmaLinux) |

## 🧩 Hints

- Enable `gather_facts: true` at the play level (otherwise `ansible_os_family`
  does not exist).
- `when:` accepts a **string** (a single condition) or a **list**
  (all ANDed):

  ```yaml
  when:
    - condition_1
    - condition_2
  ```

- For `cond-feature`, you need **2 checks**:
  1. `enable_feature is defined` (otherwise undefined variable error)
  2. `enable_feature | bool` (forces the conversion to boolean)

## 🧩 Skeleton

```yaml
---
- name: Challenge - conditions when
  hosts: db1.lab
  become: true
  gather_facts: true

  tasks:
    - name: cond-redhat (uniquement si famille RedHat)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when: ???

    - name: cond-alma9 (AlmaLinux >= 9)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when:
        - ???
        - ???

    - name: cond-feature (extra-vars enable_feature=true)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when:
        - ???
        - ???

    - name: cond-debian (ne sera PAS exécuté sur AlmaLinux)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      when: ???
```

> 💡 **Traps**:
>
> - **`when:` accepts a Jinja2 expression without `{{ }}`**: write
>   `when: my_var == "x"` directly, **not** `when: "{{ my_var == 'x' }}"`.
> - **Bool from `--extra-vars`**: `enable_feature=true` is a
>   **string**. Compare with `enable_feature | bool` or
>   `enable_feature == "true"`.
> - **`when:` on a loop**: the condition is evaluated **per item** (filtered
>   loop). To skip the whole loop, use `when:` on the parent
>   task + `block:`.
> - **`is defined`** vs **`is not none`**: `defined` tests the presence
>   of the variable, `not none` tests its value. Subtle but
>   important difference.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/conditions-when/challenge/solution.yml \
    --extra-vars "enable_feature=true"
```

🔍 Expected output: `ok=4, changed=3, skipped=1` (the debian task is
skipped).

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/conditions-when/challenge/tests/
```

> ⚠️ The root `conftest.py` automatically plays your `solution.yml` with
> `--extra-vars "enable_feature=true"` (see `_EXTRA_ARGS`).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-conditions-when
```

## 💡 Going further

- **`when:` on a `block:`**: applies the condition to all the tasks of the
  block. DRY when you have 5 tasks that share the same condition.
- **`is search` / `is match`**: Jinja2 tests for conditions on regexes
  (ex: `when: ansible_kernel is search('rhel|alma')`).
- **`failed_when` / `changed_when`**: conditions that modify the **state** of
  the task (lab 23).
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/conditions-when/challenge/solution.yml
   ```
