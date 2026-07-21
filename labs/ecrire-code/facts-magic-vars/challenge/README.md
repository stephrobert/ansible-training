# 🎯 Challenge — Facts summary via `hostvars`

## ✅ Objective

Write `challenge/solution.yml` that, on **db1.lab**, places a file
`/tmp/facts-summary.txt` containing 5 pieces of information aggregated **from 2
different hosts**: db1's local facts + web1's IP read via `hostvars`.

Expected content:

```text
db1_hostname=db1.lab
db1_os=AlmaLinux
db1_memory=<entier>
webservers_count=2
web1_ip=<web1 real IPv4, read from its facts>
```

## 🧩 Key piece: `hostvars`

`hostvars` is a **global** dictionary that contains the variables (and facts)
of **all** the hosts that Ansible has already *gathered* in the current run.

> ⚠️ **To read `hostvars['web1.lab'].ansible_default_ipv4.address`**, web1 must
> have been **gathered beforehand**. Otherwise, `hostvars['web1.lab']`
> only contains the static vars of the inventory: not the facts.

## 🧩 Pattern to use: 2 plays

The solution.yml contains **two consecutive plays**:

```yaml
---
# Play 1: pre-gather on web1 (makes its facts visible in hostvars)
- name: Pre-gather web1
  hosts: web1.lab
  gather_facts: true
  tasks: []

# Play 2: summary on db1
- name: Synthèse sur db1
  hosts: db1.lab
  become: true
  gather_facts: true
  tasks:
    - name: Poser /tmp/facts-summary.txt
      ansible.builtin.copy:
        dest: /tmp/facts-summary.txt
        mode: "0644"
        content: |
          db1_hostname={{ ??? }}
          db1_os={{ ??? }}
          db1_memory={{ ??? }}
          webservers_count={{ ??? }}
          web1_ip={{ ??? }}
```

## 🧩 Magic variables to use

| Field | Ansible variable |
| --- | --- |
| `db1_hostname` | `inventory_hostname` (magic variable, the short name from the inventory) |
| `db1_os` | `ansible_distribution` (fact, e.g. `AlmaLinux`) |
| `db1_memory` | `ansible_memtotal_mb` (fact, integer) |
| `webservers_count` | `groups['webservers'] \| length` (magic variable: list of the group's hosts) |
| `web1_ip` | `hostvars['web1.lab'].ansible_default_ipv4.address` |

> 💡 **Traps**:
>
> - **`gather_facts: true`** mandatory to use `ansible_*`. If it
>   is `false`, the facts are absent and templating crashes on
>   `'ansible_distribution' is undefined`.
> - **`hostvars[...]`**: to access another host's facts, the other
>   host must already have gathered facts. If not in the current play,
>   use `delegate_to: <host>` + `delegate_facts: true` beforehand.
> - **`groups[]`** returns a **list**, not a dict. `length` filters
>   to count, `[0]` to take the first.
> - **`ansible_default_ipv4.address`** vs `ansible_all_ipv4_addresses`:
>   the first is the IP of the default route, the second the full
>   list. Choose depending on the context.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/facts-magic-vars/challenge/solution.yml
ansible db1.lab -m ansible.builtin.command -a "cat /tmp/facts-summary.txt"
```

🔍 Check that the 5 lines are present with the right values.

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/facts-magic-vars/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-facts-magic-vars
```

## 💡 Going further

- **Fact cache**: if you have configured a fact cache (`fact_caching:
  jsonfile` in `ansible.cfg`, which is the case in this repo), the pre-gather of
  web1 is no longer necessary on the 2nd run, the facts are **read from the
  cache**. Demonstrate it by removing the 1st play and rerunning.
- **`magic_variables`**: `ansible_play_hosts`, `play_hosts`, `groups['all']`,
  `inventory_hostname_short`. Inspect them with `debug: var=...`.
- **Lint**:

   ```bash
   ansible-lint labs/ecrire-code/facts-magic-vars/challenge/solution.yml
   ```
