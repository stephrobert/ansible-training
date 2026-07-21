# Lab 56 — Host patterns (`web*`, `&prod`, `:`, `!`)

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" attendus
> ```

## 🧠 Recap

🔗 [**Ansible host patterns**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/patterns-hotes/)

**`--limit`** and the pattern operators let you target **precisely** the hosts you want without touching the playbook. Four essential operators:

| Operator | Effect | Example |
|---|---|---|
| **`:`** | Union (logical OR) | `webservers:dbservers` = web1 + web2 + db1 |
| **`:&`** | Intersection (logical AND) | `webservers:&staging` = web1 (present in both) |
| **`:!`** | Exclusion | `webservers:!web1.lab` = web2 |
| **`*`** | Wildcard | `web*.lab` = web1.lab + web2.lab |

At the RHCE exam, knowing how to target precisely is **mandatory** so as not to run a dangerous task on the wrong host.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. List the hosts targeted by a pattern with **`--list-hosts`** (without running anything).
2. Combine **union**, **intersection**, **exclusion** in a single pattern.
3. Use **wildcards** (`*`) to match names.
4. Apply **`--limit`** on a playbook to reduce the scope.
5. Understand the **priority order** of the operators.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING/labs/inventaires/patterns-hotes
ansible-inventory -i inventory/hosts.yml --graph
```

The inventory of this lab has **6 groups**: `webservers`, `dbservers`, `prod` (parent), `staging`, `monitoring`, plus the automatic `@ungrouped`. Some hosts belong to **several groups**, and that is what makes the intersections interesting.

## ⚙️ Target tree

```text
labs/inventaires/patterns-hotes/
├── README.md           ← this file
├── inventory/
│   └── hosts.yml       ← inventory with multi-group hosts
└── challenge/
    ├── README.md
    ├── solution.yml    ← playbook that lays down a marker on each host
    └── tests/
        └── test_patterns.py
```

## 📚 Exercise 1 — Discover the inventory

```bash
ansible-inventory -i inventory/hosts.yml --graph
```

Note the multiple membership: **`web1.lab`** is in `webservers`, `prod` (via children), and `staging`. **`db1.lab`** is in `dbservers`, `prod`, and `monitoring`.

🔍 **Observation**: Ansible allows a host to be in **as many groups** as you want. This is what makes the intersections powerful.

## 📚 Exercise 2 — Pattern `all`

```bash
ansible all -i inventory/hosts.yml --list-hosts
```

Output: `web1.lab`, `web2.lab`, `db1.lab`. **`all`** is the implicit root group.

## 📚 Exercise 3 — Union with `:`

```bash
ansible 'webservers:dbservers' -i inventory/hosts.yml --list-hosts
```

Output: `web1.lab`, `web2.lab`, `db1.lab`. The **union** returns all the hosts of the two groups.

🔍 **Observation**: the **single quotes** are **mandatory** around the pattern: without them, the shell interprets the `:` as a file separator or something else.

## 📚 Exercise 4 — Intersection with `:&`

```bash
ansible 'webservers:&staging' -i inventory/hosts.yml --list-hosts
```

Output: **`web1.lab`** only. The **intersection** returns the hosts present **in both** groups. `web1.lab` is in `webservers` AND in `staging`. `web2.lab` is in `webservers` but **not** in `staging` → excluded.

🔍 **Observation**: a valuable pattern for **surgical** actions, for example deploying a patch only on the machines that are **both** webservers AND in staging.

## 📚 Exercise 5 — Exclusion with `:!`

```bash
ansible 'webservers:!web1.lab' -i inventory/hosts.yml --list-hosts
```

Output: **`web2.lab`** only. **`!web1.lab`** removes `web1.lab` from the group.

```bash
ansible 'all:!dbservers' -i inventory/hosts.yml --list-hosts
```

Output: `web1.lab`, `web2.lab`. All **except** the dbservers.

## 📚 Exercise 6 — Wildcards

```bash
ansible 'web*.lab' -i inventory/hosts.yml --list-hosts
```

Output: `web1.lab`, `web2.lab`. The **wildcard `*`** matches any sequence of characters.

```bash
ansible '*1.lab' -i inventory/hosts.yml --list-hosts
```

Output: `web1.lab`, `db1.lab`. All the hosts that end with `1.lab`.

## 📚 Exercise 7 — Complex combinations

```bash
ansible 'prod:!monitoring' -i inventory/hosts.yml --list-hosts
```

Output: `web1.lab`, `web2.lab`. All the hosts of prod **except** those in monitoring (db1).

```bash
ansible 'webservers:dbservers:!staging' -i inventory/hosts.yml --list-hosts
```

Output: `web2.lab`, `db1.lab`. Union of webservers and dbservers, **minus** those in staging (web1).

🔍 **Observation**: the operators are evaluated **from left to right**. For complex patterns, **test with `--list-hosts` first** before running the real playbook.

## 📚 Exercise 8 — `--limit` on a playbook

`--limit` applies the pattern **on top of** what is in the `hosts:` of the playbook:

```bash
ansible-playbook -i inventory/hosts.yml challenge/solution.yml --limit 'webservers:!web1.lab'
```

The playbook targets `hosts: all` but `--limit` reduces it to **`web2.lab`** only.

## 🔍 Observations to note

- **Idempotence**: a second run of your solution must show `changed=0`
  everywhere in the `PLAY RECAP`. This is the mechanical signal of a playbook
  that follows best practices.
- **Explicit FQCN**: always prefer `ansible.builtin.<module>` (or the
  appropriate collection) over the short name: `ansible-lint --profile
  production` checks it.
- **Targeting convention**: this lab targets all (4 VMs with patterns); to
  adapt to another group, adjust `hosts:` in `lab.yml`/`solution.yml` then
  rerun.
- **Isolated reset**: `dsoxlab clean <lab-id>` at the root of the lab cleanly
  uninstalls what the solution set down so you can replay the scenario.

## 🤔 Reflection questions

1. Which command will run a task on **all the servers except `web1.lab` and `db1.lab`**?
2. How do you target **only the hosts present in `prod` AND in `monitoring`**?
3. If you have 50 webservers named `web01` to `web50`, how do you target **only `web10` to `web20`**? (Hint: combine ranges and exclusion).

## 🚀 Final challenge

The challenge ([`challenge/README.md`](challenge/README.md)) asks you to write 3 `ansible-playbook --limit ...` commands that lay down marker files **only on the expected hosts** for each pattern. Automated tests via `pytest+testinfra`:

```bash
pytest -v challenge/tests/
```

## 💡 Going further

- **Ranges in patterns**: `web[01:05].lab` matches `web01.lab` to `web05.lab`.
- **Regex**: prefix with `~` (`~web[1-3]\.lab`), rarely used but it exists.
- **`ansible-inventory -i ... --list --limit '...'`**: shows the result of a pattern without running.
- **Precedence**: `:` is an OR, `:&` is AND, `:!` is NOT, evaluated from left to right.

## 🔍 Linting with `ansible-lint`

Before running pytest, validate the quality of your `lab.yml` and your
`challenge/solution.yml` with **`ansible-lint`**:

```bash
ansible-lint labs/inventaires/patterns-hotes/lab.yml
ansible-lint labs/inventaires/patterns-hotes/challenge/solution.yml
ansible-lint --profile production labs/inventaires/patterns-hotes/challenge/solution.yml
```

If `ansible-lint` returns `Passed: 0 failure(s), 0 warning(s)`, your code
follows best practices: explicit FQCN, `name:` on every task, file modes as
strings, idempotence respected, deprecated modules avoided.

> 💡 **CI tip**: integrate `ansible-lint --profile production` into a
> pre-commit hook to block any commit that would introduce anti-patterns.
