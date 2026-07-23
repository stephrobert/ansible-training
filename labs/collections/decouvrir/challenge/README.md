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

## 🧩 Stuck?

```bash
dsoxlab hint collections-decouvrir
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

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
