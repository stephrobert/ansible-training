# 🎯 Challenge — Precedence: two duels to settle

## ✅ Objective

Demonstrate **two** things in a single run, with **two** variables:

1. **`winner`**: `--extra-vars` (level 22) is stronger than the play `vars:`
   (level 12) **and** than `vars_files:` (level 14).
2. **`duel`**: between the play `vars:` (level 12) and `vars_files:` (level 14),
   **`vars_files:` wins**. This is the counter-intuitive result of the lab, and
   nobody passes `--extra-vars` on `duel`: it plays out on its own.

You will therefore stack these variables at several levels, run the play
with `--extra-vars` on **`winner` only**, and read the two results.

## 🧩 Files to create

### 1) `challenge/vars/loader.yml`

```yaml
---
winner: "vars_files"
duel: "vars_files"
```

### 2) `challenge/solution.yml`

Skeleton to complete:

```yaml
---
- name: Challenge - precedence des variables
  hosts: ???
  become: ???

  vars:
    winner: "play_vars"               # level 12
    duel: "play_vars"                 # level 12

  vars_files:
    - ???                             # vars/loader.yml: level 14

  tasks:
    - name: Poser /tmp/precedence-result.txt avec les valeurs résolues
      ansible.builtin.copy:
        dest: ???
        content: |
          winner={{ ??? }}
          duel={{ ??? }}
        mode: "0644"
```

> 💡 **Traps**:
>
> - **Level 22 = top of the top**: `--extra-vars` wins over **all** the
>   other sources (vars:, vars_files:, group_vars, host_vars,
>   set_fact...). This is what makes CLI parameters perfect for a
>   one-off override without touching the code.
> - **The test expects `winner=extra_vars_wins`**. The conftest passes
>   `--extra-vars "winner=extra_vars_wins"` automatically. If you
>   run without it, `winner` will be `vars_files` (and not `play_vars`:
>   see the next trap).
> - **`vars_files:` (14) is STRONGER than the play `vars:` (12)**:
>   exactly the opposite of naive intuition, which would want what is
>   written in the play to win over an auxiliary file. This is **what** you
>   must memorize for the EX294, and it is what `duel` proves: the test
>   expects `duel=vars_files`.
> - **Do not cheat on `duel`**: the only way to get
>   `duel=vars_files` is to declare it **in both places** and to
>   let precedence settle it. Declaring it only in
>   `vars/loader.yml` would make the test pass without demonstrating anything.

## 🚀 Run (with --extra-vars)

```bash
ansible-playbook labs/ecrire-code/precedence-variables/challenge/solution.yml \
    --extra-vars "winner=extra_vars_wins"
```

🔍 Check:

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/precedence-result.txt"
# Must display:
#   winner=extra_vars_wins
#   duel=vars_files
```

Two readings in this file:

- `winner=extra_vars_wins`: `--extra-vars` (level 22) **overrides** both
  the play `vars:` (12) and `vars_files:` (14). Nothing resists it.
- `duel=vars_files`: without `--extra-vars` to arbitrate, **`vars_files:` (14)
  beats the play `vars:` (12)**. There is the real lesson of the lab.

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/precedence-variables/challenge/tests/
```

> ⚠️ The root `conftest.py` automatically plays your `solution.yml` with
> `--extra-vars "winner=extra_vars_wins"` (see `_EXTRA_ARGS`).

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-precedence-variables
```

## 💡 Going further

- **Without `--extra-vars`**: rerun without the flag. `winner` then switches to
  `vars_files`, for the same reason as `duel`: **`vars_files:` (14) wins**
  over the play `vars:` (12). See the official precedence table in the doc.
- **How to make the play win, then?** Not with `vars:`. You have to go
  above 14: `set_fact` (19), or `task vars` (17) on the task.
- **`set_fact`**: level 19 (above `vars:`, `vars_files:` and
  `include_vars`, but under `--extra-vars`). Place a
  `set_fact: duel: "set_fact_wins"` in a task **before** the one that lays down the
  file, and observe.
- **`include_vars`** vs `vars_files:`: `include_vars` is level 18, so
  **stronger** than `vars_files:` (14). But it stays **under** `set_fact` (19),
  and this even if the `include_vars` executes after: the level takes precedence over the
  chronological order.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/precedence-variables/challenge/solution.yml
   ```
