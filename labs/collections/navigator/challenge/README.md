# 🎯 Challenge — Discover, use, and validate with `ansible-navigator`

## ✅ Objective

Write `challenge/solution.yml` (play targeting `db1.lab`) that uses **Automation
content navigator** for the whole loop and leaves the following state.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Exploration proof | `/tmp/lab-navigator-doc.txt`, `0644`, owner `root`, contains `ansible.posix.sysctl` |
| Kernel state | `vm.swappiness = 42`, live **and** written under `/etc/sysctl.d/70-navigator-lab.conf` |
| Inventory proof | `/tmp/lab-navigator-inventory.txt`, `0644`, owner `root`, contains `db1.lab` and the group `webservers` |
| Idempotency | A second run reports `changed=0` |

`ansible-navigator` runs on the **control node**: call it with `delegate_to:
localhost` and `become: false`. Pass `--mode stdout --execution-environment false`
so it stays scriptable and does not pull an EE image.

## 🧩 Stuck?

```bash
dsoxlab hint collections-navigator
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
ansible-playbook labs/collections/navigator/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/navigator/challenge/tests/
```

The pytest+testinfra test validates:

- the exploration proof exists (`0644`, root) and cites `ansible.posix.sysctl`;
- `vm.swappiness` is `42` live on `db1.lab` and persisted under `/etc/sysctl.d/`;
- the inventory proof resolves `db1.lab` and the `webservers` group;
- the solution is **idempotent** (RHCE criterion).

## 🧹 Reset

```bash
dsoxlab clean collections-navigator
```
