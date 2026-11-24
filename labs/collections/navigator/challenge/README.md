# One tool to find the module, use it, and check the inventory

## The situation

Your team is standardising on **Automation content navigator**. The old reflex was
`ansible-doc` here, `ansible-inventory` there, `ansible-playbook` to finish: three
commands, three behaviours, nothing that maps to what production actually runs
(Execution Environments). The RHCE exam now expects you to reach for
`ansible-navigator` for the whole loop.

A colleague needs a kernel parameter set on **db1.lab** but does not remember which
module does it or which collection ships it. Rather than guessing, you will *find*
the module with the navigator, then *use* it, then *validate* the inventory the play
will target, all with the same tool.

Your mission, from **control-node.lab**:

1. Use `ansible-navigator doc` to find the module that manages `sysctl` entries,
   confirm the collection it comes from, and keep a **proof** of that exploration
   on `db1.lab` (the module's fully qualified name must appear in it).
2. Use that discovered module to set `vm.swappiness = 42` on `db1.lab`, live and
   persistent, in an idempotent way.
3. Write a small inventory and validate it with `ansible-navigator inventory
   --list`, then keep the resolved output as proof on `db1.lab`.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/ansible-navigator/ (in French)

## 🎯 Challenge — Discover, use, and validate with `ansible-navigator`

### ✅ Objective

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

### 🧩 Stuck?

```bash
dsoxlab hint collections-navigator
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/collections/navigator/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/collections/navigator/challenge/tests/
```

The pytest+testinfra test validates:

- the exploration proof exists (`0644`, root) and cites `ansible.posix.sysctl`;
- `vm.swappiness` is `42` live on `db1.lab` and persisted under `/etc/sysctl.d/`;
- the inventory proof resolves `db1.lab` and the `webservers` group;
- the solution is **idempotent** (RHCE criterion).

### 🧹 Reset

```bash
dsoxlab clean collections-navigator
```
