# Target the right hosts without editing the playbook every time

## The situation

The same playbook has to run on a different perimeter every time: only the web
servers under test, the web tier except the one host being investigated, the
whole fleet except staging. The current habit is to edit the `hosts:` line
before each run, and the accident everyone saw coming happened last week: a
leftover perimeter, and the play went out on every server. The playbook must
stop knowing who it targets. That decision belongs at **run time**, from
**control-node.lab**.

Your mission:

1. Write a play targeting **all hosts**, dropping a marker named after each
   host: no perimeter hardcoded in the YAML.
2. Get the filtering done at **run time**, so the same file serves the three
   perimeters without a single edit.
3. Hit exactly three targets: the **intersection** of the web tier and staging,
   the web tier **minus** one specific host, and the whole fleet **excluding**
   staging.
4. Prove the aim: only the expected hosts carry the marker, and the others were
   never touched.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/inventaires/patterns-hotes/ (in French)

## 🎯 Challenge — Target precisely via patterns

You have seen each pattern operator individually. The challenge is to **combine** several operators and to **prove** that only the expected hosts receive the marker.

### ✅ Objective

Write `solution.yml` that:

1. Targets **`hosts: all`** (the filtering is done via `--limit` at run time).
2. Lays down a marker file `/tmp/lab56-mark-{{ inventory_hostname }}.txt` that contains `pattern OK on {{ inventory_hostname }}`.

The automated test **runs 3 commands** with different `--limit` values and checks that **only the expected hosts** received the marker:

| Run | `--limit` | Expected hosts |
|---|---|---|
| 1 | `webservers:&staging` | `web1.lab` only |
| 2 | `webservers:!web1.lab` | `web2.lab` only |
| 3 | `all:!staging` | `web2.lab`, `db1.lab` (not web1) |

> ✍️ **Compose these patterns yourself before running the tests.** The table
> above is the test's specification, not a list to copy blindly: `:&`
> (intersection) and `:!` (exclusion) are exactly the skill this lab
> teaches, and the test composes them for you. Run the three by hand first,
> and check who actually received the marker:
>
> ```bash
> ansible-playbook -i inventory/hosts.yml challenge/solution.yml --limit 'webservers:&staging'
> ansible -i inventory/hosts.yml all -m ansible.builtin.shell -a 'ls /tmp/lab56-mark-*'
> ```
>
> `ansible-playbook --limit <pattern> --list-hosts` shows the targets without
> changing anything: use it to try a pattern out before running it.

### 🧩 Instructions

Skeleton to complete:

```yaml
---
- name: Challenge — patterns d'hôtes (le filtrage se fait via --limit)
  hosts: ???                       # 'all': we target broad, --limit does the filtering
  become: ???
  gather_facts: false
  tasks:
    - name: Poser le marqueur
      ansible.builtin.copy:
        dest: ???                  # /tmp/lab56-mark-<inventory_hostname>.txt
        content: "pattern OK on {{ ??? }}\n"
        mode: "0644"
```

> 💡 **Traps**:
>
> - **`hosts: all` + `--limit`** vs **`hosts: <pattern>`**: prefer `hosts: all`
>   in the playbook and **pass the filter at runtime** via `--limit`.
>   Otherwise, you have to edit the YAML for each target: an anti-pattern.
> - **The operators**: `:` = union, `&` = intersection, `!` = exclusion,
>   `*` = wildcard. Combine them carefully: `webservers:&staging` = "in
>   webservers AND in staging".
> - **The lab inventory** defines a `staging` group that contains only
>   `web1.lab`. Check with `ansible-inventory -i ... --graph` before running
>   the playbook.
> - **`changed_when` not necessary**: `copy:` is natively idempotent on the
>   content.

Run the first demo manually to validate:

```bash
cd labs/inventaires/patterns-hotes/
ansible-playbook -i inventory/hosts.yml challenge/solution.yml \
    --limit 'webservers:&staging'
ssh -F ~/.cache/dsoxlab/ansible-training/ssh_config web1.lab cat /tmp/lab56-mark-web1.lab.txt
```

The pytest test automatically applies the 3 patterns one after another.

### 🧪 Validation

```bash
pytest -v challenge/tests/
```

### 🚀 Going further

- Add a 4th test case: `--limit '*1.lab'` (should touch `web1.lab` AND `db1.lab`).
- Modify the inventory to add a `dev` group containing `web1.lab` and `db1.lab`. Test `dev:!monitoring` (= web1, because db1 is in monitoring).
- Compare the outputs of `--list-hosts` and `--limit`: the first does a dry-run of the resolution, the second applies it.

---

Good luck! 🧠

### 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean inventaires-patterns-hotes
```

This target uninstalls/removes what the solution set down on the managed nodes
(packages, files, services, firewall rules) so that you can rerun the solution
from scratch.
