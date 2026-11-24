# "Module not found", and the module is right there

## The situation

A playbook that has worked for two years fails on the new control node: module
not found. The module exists, it is just called by its short name, and the
collection that provides it is not installed here. Nobody can say which
collections this environment actually carries, or where they came from. Meanwhile
the linter has started rejecting short names outright, so "it used to work" is
about to stop being an argument across the whole codebase.

Your mission, from **control-node.lab**:

1. Take inventory of the collections actually installed in the environment, with
   their **versions** and where they live on disk, and have the play write that
   inventory to a file on **db1.lab** rather than to your scrollback.
2. Read a collection's own metadata to find who publishes it, which version it
   claims, and what it depends on.
3. Walk its layout and say what a collection can ship beyond modules: plugins,
   roles, playbooks, docs.
4. Take a module you call every day, find the collection it comes from, and write
   its **fully qualified name**. That is what the linter will demand tomorrow.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ (in French)

## 🎯 Challenge — Inventory of installed collections

### ✅ Objective

Deposit on `db1.lab` a file `/tmp/lab93-collections.txt` that contains the inventory of the installed collections with their **versions** and their **path**, generated dynamically by Ansible.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab93-collections.txt` |
| Permissions | `0644`, owner `root` |
| Content | At least 3 collections listed (`ansible.posix`, `community.general`, `kubernetes.core` or others present in the EE) |
| Format | One collection per line, format `<FQCN_namespace.name> <version>` (e.g. `community.general 10.5.0`) |
| Method | Use `ansible.builtin.command` to invoke `ansible-galaxy collection list` then `register:` + `copy` |

### 🧩 Stuck?

```bash
dsoxlab hint collections-decouvrir
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

From the repo root:

```bash
ansible-playbook labs/collections/decouvrir/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/collections/decouvrir/challenge/tests/
```

The pytest+testinfra test validates:

- `/tmp/lab93-collections.txt` exists with mode `0644`, owner `root`.
- At least 3 non-empty lines.
- At least one line contains an FQCN with a dot (e.g. `community.general`).
- The solution is **idempotent**: a second run reports no change (RHCE criterion).

### 🧹 Reset

```bash
dsoxlab clean collections-decouvrir
```

### 💡 Going further

- **Lab 94**: `requirements.yml` to reproduce the environment.
- **`ansible-galaxy collection list --format json`**: scriptable output for CI integration.
- **`ansible-lint --profile production`**: zero warning expected.
