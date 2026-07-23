# Lab 15 — Variable precedence (22 RHCE EX294 levels)

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

🔗 [**Ansible variable precedence (the 22 official levels)**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/precedence-variables/)

Ansible defines **22 precedence levels** for variables. When the same
variable is defined in several places, the **highest level wins**. This
mechanic is **explicitly tested at the RHCE EX294**, it is a classic trap:
"I did define `app_env: prod` in `vars:` but Ansible sees `dev`!". The answer
is almost always in the precedence.

The official order (from weakest to strongest), as the Ansible doc gives it,
[« Understanding variable precedence »](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence):

```
role defaults (2)
< group_vars all (4 inventory, 5 playbook)
< group_vars groups (6 inventory, 7 playbook)
< host_vars (9 inventory, 10 playbook)
< cached facts / set_facts (11)
< play vars: (12)
< vars_prompt (13)
< vars_files: (14)
< role vars, roles/<role>/vars/main.yml (15)
< block vars (16)
< task vars (17)
< include_vars (18)
< set_fact / registered variables (19)
< role params (20)
< include params (21)
< -e --extra-vars (22, wins over EVERYTHING)
```

⚠️ **The trap that costs the most**: `vars_files:` (14) **beats** the play
`vars:` (12). Intuition says the opposite ("what I write in my play is
closer, so stronger"), and it is wrong. The loaded file wins. This is
**what** you must memorize for the EX294, and it is what you will measure in
exercise 3.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. **Demonstrate** mechanically which level wins by stacking the same variable.
2. **Understand** why `--extra-vars` is the final weapon.
3. **Distinguish** the play `vars:` (level 12) from `vars_files:` (level 14), and
   know **which one wins** when both carry the same variable.
4. **Diagnose** a variable that "does not take the expected value".
5. **Choose** the right level for each case (default, env override, CLI override).

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
mkdir -p labs/ecrire-code/precedence-variables/{group_vars,host_vars,vars}
ansible db1.lab -m ping
```

## 📚 Exercise 1 — Basic demonstration: 3 levels

Create `group_vars/all.yml`:

```yaml
---
priority_test: "from_group_vars_all"
```

Create `group_vars/dbservers.yml`:

```yaml
---
priority_test: "from_group_vars_dbservers"
```

Create `lab.yml`:

```yaml
---
- name: Demo precedence
  hosts: db1.lab
  become: true
  vars:
    priority_test: "from_play_vars"
  tasks:
    - name: Quelle valeur gagne ?
      ansible.builtin.debug:
        var: priority_test
```

**Before running**, **guess**: who wins?

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation**: `priority_test = from_play_vars`. Why? Because
these `group_vars/` are placed next to the playbook, so:

- `group_vars/all.yml` (level 5) ← the weakest of the three.
- `group_vars/dbservers.yml` (level 7) ← beats all (more specific group).
- **play `vars:` (level 12) ← beats the group_vars**.

## 📚 Exercise 2 — Add `host_vars/`

Create `host_vars/db1.lab.yml`:

```yaml
---
priority_test: "from_host_vars"
```

**Rerun**:

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation**: still `from_play_vars`. Why? `host_vars/` (level 10
here, placed next to the playbook) is more specific than `group_vars/`, but
**still lower priority than the play `vars:` (level 12)**.

**Takeaway**: all the **inventory specificity** (host > group) stays
**under** the play. As soon as a variable is written in the play, the inventory
no longer takes it over. Careful: this does not mean the play `vars:` are
unbeatable, exercise 3 shows it.

## 📚 Exercise 3 — `vars_files:` (14) against the play `vars:` (12)

This is **the** duel of the lab, and the one intuition loses. Create `vars/loader.yml`:

```yaml
---
priority_test: "from_vars_files"
```

Modify `lab.yml` to load this file **in addition to** the play `vars:`:

```yaml
---
- name: Demo precedence vars_files
  hosts: db1.lab
  become: true
  vars:
    priority_test: "from_play_vars"
  vars_files:
    - vars/loader.yml
  tasks:
    - name: Quelle valeur gagne ?
      ansible.builtin.debug:
        var: priority_test
```

**Before running**, place your bet. Most people bet `from_play_vars`: the
`vars:` is written in the play, in plain sight, while the file is "next to
it". Run:

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation**: `priority_test = from_vars_files`. **`vars_files:`
(level 14) beats the play `vars:` (level 12)**, and there is no exception:
the declaration order in the play changes nothing, putting `vars_files:` before
or after `vars:` does not either. The level alone decides.

**Why this direction?** The play `vars:` are designed as **default values of
the play**; a `vars_files:` is an **operations decision** (the environment, the
site, the client). It is therefore normal that the file wins: it is the one
that carries the choice, the play only carries the fallback.

**To memorize for the EX294**: if you place a value in `vars:` and it "does
not take", look for a `vars_files:` before blaming Ansible. And if you
want a play value to be **unbeatable** by a file, it is not `vars:` you
must use, but a higher level (`set_fact`, exercise 4).

## 📚 Exercise 4 — Add `set_fact` (level 19)

Modify `lab.yml` to add a `set_fact`:

```yaml
- name: Demo precedence avec set_fact
  hosts: db1.lab
  become: true
  vars:
    priority_test: "from_play_vars"
  tasks:
    - name: Forcer la valeur via set_fact
      ansible.builtin.set_fact:
        priority_test: "from_set_fact"

    - name: Quelle valeur gagne maintenant ?
      ansible.builtin.debug:
        var: priority_test
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation**: `priority_test = from_set_fact`. **`set_fact` (level 19)**
beats the **play `vars:` (level 12)** and also the **`vars_files:` (level 14)** from
the previous exercise. This is useful when you want to **compute** a variable
from others and this value **must win** over the defaults as over
the files.

## 📚 Exercise 5 — `--extra-vars` (level 22, the final weapon)

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml \
  --extra-vars "priority_test=from_extra_vars"
```

🔍 **Observation**: `priority_test = from_extra_vars`. **`--extra-vars` (level 22)
beats even `set_fact` (level 19)**. No mechanism in the playbook can override
`--extra-vars`.

**Typical use case**: an operator forces a value during an emergency run without
modifying the code, or the CI/CD passes `--extra-vars` computed from the environment.

## 📚 Exercise 6 — The dict trap: merge vs override

With a **dict**, precedence does not do a smart merge, it **completely
replaces**. Demonstration:

Create `group_vars/dbservers-dict.yml`:

```yaml
---
db_config:
  host: db1.lab
  port: 5432
  pool_size: 10
```

Modify `lab.yml`:

```yaml
- name: Demo precedence dicts
  hosts: db1.lab
  vars:
    db_config:
      host: db1.lab
      port: 5432
      timeout: 30
  tasks:
    - name: Afficher le dict resultant
      ansible.builtin.debug:
        var: db_config
```

**Run**:

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml
```

🔍 **Observation**: `db_config` has **3 keys**: `host`, `port`, `timeout`. **NO
`pool_size`**. Why? Because the play `vars:` **completely replaced** the
dict of the group_vars, no merge.

**Solution**: use the **`combine`** filter or enable
`hash_behaviour = merge` in `ansible.cfg` (not recommended because implicit and global).

```yaml
vars:
  db_config: "{{ db_config_base | combine({'timeout': 30}, recursive=True) }}"
```

## 📚 Exercise 7 — Diagnosis: why is my variable weird?

Tool number 1: display **all the vars** seen by Ansible:

```bash
ansible-playbook labs/ecrire-code/precedence-variables/lab.yml -vvv 2>&1 | grep -A2 "priority_test"
```

🔍 **Observation**: with `-vvv`, Ansible displays the loaded vars and their source.
Look for the **last** mention of `priority_test`, it is the effective value.

Tool number 2: place a `debug:` at the start and the end of the play to compare:

```yaml
- name: Diagnostic debut play
  ansible.builtin.debug:
    var: priority_test

# ... your tasks ...

- name: Diagnostic fin play
  ansible.builtin.debug:
    var: priority_test
```

If the value changes between the two, it means an intermediate `set_fact` or
`register: + with_*` hit it.

## 🔍 Observations to note

- **`--extra-vars` (22)** > `role params` (20) > `set_fact` (19) > `include_vars` (18) > `role vars` (15) > **`vars_files:` (14)** > **play `vars:` (12)** > `facts` (11) > `host_vars` (9-10) > `group_vars/<grp>` (6-7) > `group_vars/all` (4-5) > `role defaults` (2).
- **`vars_files:` (14) BEATS the play `vars:` (12)**. This is the counter-intuitive point of the lab: the loaded file wins over what is written in the play.
- **Inventory specificity** (host > group) **does not beat** the play: all the inventory stays under level 12.
- **Dicts** are **not merged** by default, a higher level **replaces** completely.
- **`combine(recursive=True)`** is the tool for a real dict merge.
- **`-vvv`** + grep lets you trace the source of a value.

## 🤔 Reflection questions

1. You want an operator to be able to force `app_env=prod` during an emergency
   deployment without touching the code. Which level do you use, and why not
   `host_vars/` (level 9-10) which seems "more official"?

2. You have a dict `database:` defined in `group_vars/all.yml` with 5 keys. You
   want to **add** a 6th key for the `dbservers` group without rewriting the 5
   first ones. How?

3. Why is `set_fact` (level 19) **higher priority** than the play `vars:`
   (level 12)? What is the **use case** that justifies this precedence?

4. A colleague claims: "my play `vars:` are the strongest thing there is,
   apart from `--extra-vars`". Give them **two** counter-examples taken from this lab,
   including one that requires **no** task to execute.

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md) for the pytest+testinfra validation.

## 💡 Going further

- **Dynamic `include_vars:`** (level 18): load a vars file according to a
  runtime condition, higher level than `vars_files:` (static, level 14).
  Careful: `set_fact` (19) stays **above** `include_vars` (18), even if
  the `include_vars` executes **after** in the play. The level takes precedence over
  the chronological order.
- **Role defaults vs role vars**: `roles/<role>/defaults/main.yml` (level 2, the
  weakest, easy to override) vs `roles/<role>/vars/main.yml` (level 15,
  above `vars_files:`, hard to override). To choose according to intent.
- **`ANSIBLE_HASH_BEHAVIOUR=merge`**: env variable that globally changes the
  behavior of dicts. **Not recommended**, prefer explicit `combine` per variable.
- **`var | default(<lookup_string>)` pattern**: chained fallback to reproduce
  a custom precedence logic.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
# Lint your lab file (guided tutorial)
ansible-lint labs/ecrire-code/precedence-variables/lab.yml

# Lint your challenge solution
ansible-lint labs/ecrire-code/precedence-variables/challenge/solution.yml

# Production profile (the strictest, RHCE 2026 target)
ansible-lint --profile production labs/ecrire-code/precedence-variables/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
