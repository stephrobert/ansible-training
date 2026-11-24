# The default that got committed as production

## The situation

The `db1.lab` playbook carries its values inside the file: service name, port,
database engine, connection limit. Last Friday someone edited that file to
point a run at production, ran it, and forgot to revert. The next colleague
pulled the repo and pushed production settings onto a test host. The values are
not the problem. Hardcoding them in one place, and **editing that place to
change a single run**, is.

You restructure it from **control-node.lab**.

Your mission:

1. Split the sources: keep the service identity in the play's **`vars:`**, move
   the database settings to an external file loaded by **`vars_files:`**.
2. Run it once with nothing on the command line, and confirm each variable
   resolves to the value coming from its own source.
3. Override two of them at run time with **`--extra-vars`**, without touching a
   single file.
4. Write the resolved values on `db1.lab` and read them back: only the two
   overridden ones moved. Then say which level wins, and why `vars_files:`
   (level 14) would beat the play's `vars:` (level 12) if both carried the same
   variable, and not the other way round.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/variables-base/ (in French)

## 🎯 Challenge — Variables and override via `--extra-vars`

### ✅ Objective

Write `challenge/solution.yml` that on **db1.lab** combines **3 sources** of
variables and demonstrates the **precedence** of `--extra-vars` (level 22, the highest).

You will create **two files**:

1. `challenge/vars/db.yml`: an external variables file.
2. `challenge/solution.yml`: the playbook that loads `vars_files:` + `vars:`.

At runtime, we pass `--extra-vars` to force 2 values and observe that they
**override** those of the play.

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-variables-base
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

#### First run — without `--extra-vars`

```bash
ansible-playbook labs/ecrire-code/variables-base/challenge/solution.yml
```

```bash
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/challenge-vars.txt"
```

🔍 You should see the 4 **default** values (see table above).

#### Second run — with `--extra-vars`

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

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/variables-base/challenge/tests/
```

> ⚠️ The root `conftest.py` automatically runs your `solution.yml` with
> `--extra-vars "service_name=production-api db_max_connections=500"` (see
> `_EXTRA_ARGS` in the conftest). That is what makes the 5 assertions green.

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-variables-base
```

### 💡 Going further

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
