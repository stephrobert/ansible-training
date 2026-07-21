# 🎯 Challenge — Inventory of installed collections

## ✅ Objective

Deposit on `db1.lab` a file `/tmp/lab93-collections.txt` that contains the inventory of the installed collections with their **versions** and their **path**, generated dynamically by Ansible.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab93-collections.txt` |
| Permissions | `0644`, owner `root` |
| Content | At least 3 collections listed (`ansible.posix`, `community.general`, `kubernetes.core` or others present in the EE) |
| Format | One collection per line, format `<FQCN_namespace.name> <version>` (e.g. `community.general 10.5.0`) |
| Method | Use `ansible.builtin.command` to invoke `ansible-galaxy collection list` then `register:` + `copy` |

## 🧩 Hints

### Step 1 — Capture the list with `ansible-galaxy`

```yaml
- name: Lister les collections installées
  ansible.builtin.command: ???                # ← command that lists the collections
  register: ???
  changed_when: ???                            # ← read only
```

### Step 2 — Filter the output to keep only the useful lines

The raw output contains headers (`Collection`, `-----`) that must be filtered. You can:

- Either use `awk` / `grep` in a shell (but then `ansible.builtin.shell`).
- Or use Ansible **Jinja2 filters** (`split`, `select`, `reject`).

Possible skeleton with Jinja2 filters:

```yaml
- name: Filtrer pour ne garder que les collections
  ansible.builtin.set_fact:
    collections_clean: "{{ collections_raw.stdout_lines
                            | reject('match', '^(#|Collection|---|$)')
                            | list }}"
```

### Step 3 — Deposit the file

```yaml
- name: Déposer l'inventaire
  ansible.builtin.copy:
    dest: /tmp/lab93-collections.txt
    content: "???"                             # ← join the lines
    owner: ???
    group: ???
    mode: ???
```

> 💡 **Pitfalls**:
>
> - **`ansible-galaxy collection list`** displays ALL the collections
>   installed (control node), not the ones **used** by a play.
>   To see the used collections: `ansible-doc -t module -l |
>   grep <namespace>`.
> - **FQCN mandatory** since Ansible 2.10+: `ansible.builtin.copy`,
>   not just `copy`. The `ansible-lint production` profile checks it.
> - **`collections:`** at play level: lets you use the modules without
>   FQCN in this play. Handy but hides the dependency: prefer FQCN.
> - **`~/.ansible/collections/`**: where the collections installed
>   per user go. For a system-wide install: `-p /usr/share/ansible/collections`.

## 🚀 Launch

From the repo root:

```bash
ansible-playbook labs/collections/decouvrir/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/decouvrir/challenge/tests/
```

The pytest+testinfra test validates:

- `/tmp/lab93-collections.txt` exists with mode `0644`, owner `root`.
- At least 3 non-empty lines.
- At least one line contains an FQCN with a dot (e.g. `community.general`).
- The solution is **idempotent**: a second run reports no change (RHCE criterion).

## 🧹 Reset

```bash
dsoxlab clean collections-decouvrir
```

## 💡 Going further

- **Lab 94**: `requirements.yml` to reproduce the environment.
- **`ansible-galaxy collection list --format json`**: scriptable output for CI integration.
- **`ansible-lint --profile production`**: zero warning expected.
