# 🎯 Challenge — Variables and override via `--extra-vars`

## ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** combines **3 sources** of
variables and demonstrates the **precedence** of `--extra-vars` (level 22, the highest).

You will create **two files**:

1. `challenge/vars/db.yml`: an external variables file.
2. `challenge/solution.yml`: the playbook that loads `vars_files:` + `vars:`.

At runtime, we pass `--extra-vars` to force 2 values and observe that they
**override** those of the play.

## 🧩 Hints

### 1) Create the `challenge/vars/db.yml` file

```yaml
---
db_engine: ???
db_max_connections: ???
```

To be completed according to the table below.

### 2) Create `challenge/solution.yml`

Skeleton:

```yaml
---
- name: Challenge - precedence variables
  hosts: db1.lab
  become: true

  vars:
    service_name: "default-service"
    service_port: 8000

  vars_files:
    - vars/db.yml

  tasks:
    - name: Poser /tmp/challenge-vars.txt avec les 4 variables résolues
      ansible.builtin.copy:
        dest: /tmp/challenge-vars.txt
        mode: "0644"
        content: |
          service_name={{ ??? }}
          service_port={{ ??? }}
          db_engine={{ ??? }}
          db_max_connections={{ ??? }}
```

### 3) Expected values in the files

| Variable | Source | Expected value (without `--extra-vars`) |
| --- | --- | --- |
| `service_name` | `vars:` of the play | `default-service` |
| `service_port` | `vars:` of the play | `8000` |
| `db_engine` | `vars_files: vars/db.yml` | `postgresql` |
| `db_max_connections` | `vars_files: vars/db.yml` | `100` |

## 🚀 Launch

### First run — without `--extra-vars`

```bash
ansible-playbook labs/ecrire-code/variables-base/challenge/solution.yml
```

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/challenge-vars.txt"
```

🔍 You should see the 4 **default** values (see table above).

### Second run — with `--extra-vars`

```bash
ansible-playbook labs/ecrire-code/variables-base/challenge/solution.yml \
    --extra-vars "service_name=production-api db_max_connections=500"
```

🔍 The file must contain:

```text
service_name=production-api    ← overridden by --extra-vars
service_port=8000              ← from the play (not overridden)
db_engine=postgresql           ← from vars_files: (not overridden)
db_max_connections=500         ← overridden by --extra-vars
```

> 💡 **Pitfalls**:
>
> - **`--extra-vars` (priority 22)** wins over **everything**. That is what makes
>   CLI params perfect for one-off overrides.
> - **Format `--extra-vars "k1=v1 k2=v2"`**: **simple** values are passed in
>   key=value format. For complex values (lists, dicts), use the JSON format
>   with `--extra-vars '{"k": [1,2]}'`.
> - **Boolean `--extra-vars "flag=true"`** is read as a **string**, not a bool.
>   Compare with `flag | bool` or `flag == "true"`, not `flag is true`.
> - **`vars_files:` (14)** > **the play's `vars:` (12)**: the loaded file
>   **wins** over what is written in the play. Counter-intuitive, and worth
>   remembering for the EX294. Here the two sources do not carry the same
>   variables, so the pitfall is not triggered; the `precedence-variables` lab
>   stages it and measures it.

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/variables-base/challenge/tests/
```

> ⚠️ The root `conftest.py` automatically runs your `solution.yml` with
> `--extra-vars "service_name=production-api db_max_connections=500"` (see
> `_EXTRA_ARGS` in the conftest). That is what makes the 5 assertions green.

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-variables-base
```

## 💡 Going further

- **Test `group_vars/all.yml`**: set `service_port: 9999` in
  `inventory/group_vars/all.yml` and rerun without `--extra-vars`. Which value
  wins? Which has higher priority between the play's `vars:` and `group_vars/all.yml`?
  (Spoiler: the play's `vars:`; see lab 15 for the complete precedence table.)
- **JSON format for `--extra-vars`**:

   ```bash
   --extra-vars '{"service_port": 9090, "tags": ["v1", "stable"]}'
   ```

   Essential to pass complex **lists** or **dicts**.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/variables-base/challenge/solution.yml
   ```
