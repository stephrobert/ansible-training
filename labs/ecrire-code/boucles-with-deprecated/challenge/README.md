# The playbook you inherited was written in 2016

## The situation

You take over a repo nobody has touched in years. It works. It also fails the
CI lint gate on its very first file: `with_items` everywhere, a `with_dict` on
the ports mapping, a `with_subelements` nobody dares read out loud. The syntax
is deprecated, not broken, which is exactly why it is still there. It will keep
working right until the release that removes it, and that release is not far
off.

You modernise the iterations on `db1.lab`, from **control-node.lab**.

Your mission:

1. Rewrite the simple list iteration with **`loop:`**, the modern one-to-one
   replacement.
2. Migrate the port mapping: a dict does **not** iterate directly. Convert it
   to a list of pairs and reach both the key and the value.
3. Keep the console readable while you are in there: label each iteration by
   what it actually does.
4. Reach zero deprecation on `ansible-lint`, and find out which of these
   rewrites the linter can perform for you.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/controle-flux/boucles-with-deprecated/ (in French)

## 🎯 Challenge — Migrate `with_*` loops to `loop:`

### ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** uses **only the
modern `loop:` form** (never `with_items:` nor `with_dict:`) for two
different iterations:

| Iteration | Source | Expected output |
| --- | --- | --- |
| Simple list | `[apple, banana, cherry]` | 3 files `/tmp/withitems-<fruit>.txt` |
| Dict (key→value) | `{nginx: 80, redis: 6379}` | `/tmp/withdict-nginx.txt` (content `80`), `/tmp/withdict-redis.txt` (content `6379`) |

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-boucles-with-deprecated
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🧩 Skeleton

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

### 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
```

🔍 Check:

```bash
ansible db1.lab -m ansible.builtin.command -a "ls /tmp/withitems-*.txt /tmp/withdict-*.txt"
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/withdict-nginx.txt"
```

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/boucles-with-deprecated/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-boucles-with-deprecated
```

### 💡 Going further

- **`with_items` → `loop`** (1-to-1); **`with_dict` → `loop: dict | dict2items`**;
  **`with_subelements` → `subelements` filter**. The Ansible docs list all
  the conversions [here](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_loops.html#migrating-from-with-x-to-loop).
- **`loop_control: index_var: i`**: expose the current index.
- **Lint**: `ansible-lint` flags `with_items` as `deprecation`.

   ```bash
   ansible-lint labs/ecrire-code/boucles-with-deprecated/challenge/solution.yml
   ```
