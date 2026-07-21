# 🎯 Challenge — Migrate `with_*` loops to `loop:`

## ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** uses **only the
modern `loop:` form** (never `with_items:` nor `with_dict:`) for two
different iterations:

| Iteration | Source | Expected output |
| --- | --- | --- |
| Simple list | `[apple, banana, cherry]` | 3 files `/tmp/withitems-<fruit>.txt` |
| Dict (key→value) | `{nginx: 80, redis: 6379}` | `/tmp/withdict-nginx.txt` (content `80`), `/tmp/withdict-redis.txt` (content `6379`) |

## 🧩 Hints

### Loop over a simple list

```yaml
loop:
  - element1
  - element2
```

The current item is accessible via `{{ item }}`.

### Loop over a dict

A dict does not iterate directly. You have to **convert it into a list of pairs**
with the **`dict2items`** filter:

```yaml
loop: "{{ mon_dict | dict2items }}"
```

Each item becomes a dict `{ key: ..., value: ... }`. You access the two
fields via `{{ item.key }}` and `{{ item.value }}`.

## 🧩 Skeleton

```yaml
---
- name: "Challenge - migration with_* vers loop:"
  hosts: db1.lab
  become: true

  vars:
    ports:
      nginx: 80
      redis: 6379

  tasks:
    - name: Itération sur liste simple (loop:)
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      loop:
        - apple
        - banana
        - cherry

    - name: Itération sur dict via dict2items
      ansible.builtin.copy:
        dest: ???
        content: ???
        mode: "0644"
      loop: ???
      loop_control:
        label: "{{ item.key }}"
```

> ⚠️ **Quote the `name:`** when it ends with `loop:` (otherwise YAML reads
> it as a key-value mapping). Hence the quotes in the skeleton.

**Additional traps**:

> - **`with_items`** is **deprecated** since Ansible 2.5 but still
>   works. On the EX294, use **`loop:`** (lab 21).
> - **`with_dict`** converts a dict into a list of dicts `{key, value}`.
>   Migration to `loop:`: `dict | dict2items` then `item.key` /
>   `item.value`.
> - **`with_subelements`**: to iterate over a sub-list of each dict.
>   Migration to `loop:`: `subelements()` filter.
> - **No double-loop**: `loop:` accepts only one dimension. For 2
>   dimensions, use the `subelements` or `product` filter.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
```

🔍 Check:

```bash
ansible db1.lab -m ansible.builtin.command -a "ls /tmp/withitems-*.txt /tmp/withdict-*.txt"
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/withdict-nginx.txt"
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/boucles-with-deprecated/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-boucles-with-deprecated
```

## 💡 Going further

- **`with_items` → `loop`** (1-to-1); **`with_dict` → `loop: dict | dict2items`**;
  **`with_subelements` → `subelements` filter**. The Ansible docs list all
  the conversions [here](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_loops.html#migrating-from-with-x-to-loop).
- **`loop_control: index_var: i`**: expose the current index.
- **Lint**: `ansible-lint` flags `with_items` as `deprecation`.

   ```bash
   ansible-lint labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
   ```
