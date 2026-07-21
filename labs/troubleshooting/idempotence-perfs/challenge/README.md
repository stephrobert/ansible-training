# 🎯 Challenge — Refactor a non-idempotent playbook

## ✅ Objective

Write a playbook that **passes the idempotence test**: `changed=0` on the second run. Three operations to chain on `db1.lab`, each **idempotent**:

| # | Action | Recommended module | Idempotence guard |
| --- | --- | --- | --- |
| 1 | Create `/tmp/lab91-marker` with content | `ansible.builtin.shell` | `creates:` |
| 2 | Set `max_connections = 200` in `/tmp/lab91-config.cfg` | `ansible.builtin.lineinfile` | `regexp:` + `create:` |
| 3 | Read the curl version and store it in `/tmp/lab91-curl.txt` | `ansible.builtin.command` + `register` + `copy` | `changed_when: false` on the read |

**Criterion**: the second run of `solution.yml` returns `changed=0`.

## 🧩 Hints

### `solution.yml` skeleton

```yaml
---
- name: Challenge 91 — playbook idempotent
  hosts: ???
  become: ???
  gather_facts: false

  tasks:
    - name: Tâche 1 — créer marker
      ansible.builtin.shell: "echo lab91 > /tmp/lab91-marker"
      args:
        creates: ???              # ← path of the marker file

    - name: Tâche 2 — poser max_connections
      ansible.builtin.lineinfile:
        path: /tmp/lab91-config.cfg
        regexp: ???               # ← regex to match the line
        line: ???
        create: ???
        mode: "0644"

    - name: Tâche 3a — lire la version curl
      ansible.builtin.command: curl --version
      register: curl_version
      changed_when: ???           # ← read-only

    - name: Tâche 3b — stocker la sortie
      ansible.builtin.copy:
        dest: /tmp/lab91-curl.txt
        content: "{{ curl_version.stdout_lines[0] }}\n"
        mode: "0644"
```

### Manual idempotence test

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml | grep -E 'changed=|ok='
# → changed=0 expected on the 2nd run
```

> 💡 **Traps**:
>
> - **`shell:` / `command:` without `creates:` or `changed_when:`**: marked
>   `changed=1` on every run → breaks the play's idempotence. The main
>   cause of a failing "changed=0 on the 2nd run" test.
> - **`pipelining = True`** in `ansible.cfg`: 30-50% speedup. But
>   incompatible with `requiretty` in sudoers, check the sudoers
>   first.
> - **`fact_caching = jsonfile`** + 1h TTL: avoids re-gathering the
>   facts on every run. Saves 1-3 sec per host.
> - **`forks` (default 5)**: raise it to 10-20 on a decent control
>   node. More parallelism = shorter run on a large inventory.
> - **`strategy: free`**: each host advances independently, faster
>   than `linear` but with less readable output.

## 🚀 Running

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/idempotence-perfs/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-idempotence-perfs
```

## 💡 Going further

- **`ansible-lint --profile production`** detects `command`/`shell` without `changed_when:`.
- **A `ansible-lint` pre-commit hook** in the repo to block regressions.
- **`--check --diff` mode** to preview changes without applying them.
