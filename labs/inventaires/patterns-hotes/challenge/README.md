# 🎯 Challenge — Target precisely via patterns

You have seen each pattern operator individually. The challenge is to **combine** several operators and to **prove** that only the expected hosts receive the marker.

## ✅ Objective

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

## 🧩 Instructions

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

## 🧪 Validation

```bash
pytest -v challenge/tests/
```

## 🚀 Going further

- Add a 4th test case: `--limit '*1.lab'` (should touch `web1.lab` AND `db1.lab`).
- Modify the inventory to add a `dev` group containing `web1.lab` and `db1.lab`. Test `dev:!monitoring` (= web1, because db1 is in monitoring).
- Compare the outputs of `--list-hosts` and `--limit`: the first does a dry-run of the resolution, the second applies it.

---

Good luck! 🧠

## 🧹 Reset

To replay the challenge in a neutral state:

```bash
dsoxlab clean inventaires-patterns-hotes
```

This target uninstalls/removes what the solution set down on the managed nodes
(packages, files, services, firewall rules) so that you can rerun the solution
from scratch.
