# Lab 000 — Prepare the managed nodes

This lab runs **automatically** at the end of `dsoxlab provision`. It prepares the 3 managed nodes (`web1`, `web2`, `db1`) so they are usable by all the playbooks of the training.

---

## 🧠 Recap and recommended reading

🔗 [**Prepare Ansible managed nodes: Python, SSH, sudo, firewall**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/premiers-pas/preparer-noeuds-geres/)

This page explains:

- The **5 prerequisites** of a managed node (Python 3, SSH by key, sudo NOPASSWD, firewall, NTP)
- The **"Ansible prepares itself"** pattern: cloud-init lays down the minimum, Ansible converges the rest
- The **bootstrap via the `raw` module** when Python 3 is not available on the target

---

> This lab is not a page of the training as such: it is an **idempotent bootstrap** that materializes the **Ansible prepares itself** principle. Cloud-init lays down only the minimum (`ansible` user + SSH key + sudo NOPASSWD). Everything else (chrony, useful packages, /etc/hosts, SELinux, timezone) is applied by this playbook.

## What `playbook.yml` does

| Task | Module | Effect |
|---|---|---|
| Install base packages | `ansible.builtin.dnf` | `python3-libselinux`, `python3-firewall`, `chrony`, `bash-completion`, `vim-enhanced`, `tar`, `rsync` |
| Start chronyd | `ansible.builtin.systemd` | Time sync active (consistency of facts between VMs) |
| Register the lab hosts | `ansible.builtin.lineinfile` | `/etc/hosts` contains `web1.lab`, `web2.lab`, `db1.lab`, `control-node.lab` |
| SELinux enforcing | `ansible.posix.selinux` | `Enforcing` mode, `targeted` policy (consistent with RHCE) |
| Timezone | `community.general.timezone` | `Europe/Paris` |

## Run manually

From the root of the lab:

```bash
ansible-playbook labs/bootstrap/prepare-managed-nodes/playbook.yml
```

or via the CLI, which lays down the starting state then validates:

```bash
dsoxlab run bootstrap-prepare-managed-nodes
dsoxlab check bootstrap-prepare-managed-nodes
```

## Idempotence

A second `dsoxlab run <lab-id>` must show `changed=0` on all nodes: this is the definition of a clean playbook. If it is not the case, the playbook rewrites something on every pass (typically: `lineinfile` with an unanchored regexp).

## Tests

Validation by `pytest + testinfra` in [`challenge/tests/test_functional.py`](./challenge/tests/test_functional.py), which checks on each managed node:

- chrony installed + chronyd active
- packages `python3-libselinux`, `python3-firewall`, `tar`, `rsync` present
- `/etc/hosts` contains the 4 entries
- SELinux in `Enforcing`
- timezone `Europe/Paris`

```bash
pytest -v labs/bootstrap/prepare-managed-nodes/challenge/tests/
```

## Why this pattern

The old [`ansible-training`](https://github.com/stephrobert/ansible-training) lab placed at the end of each exercise a challenge self-validated by `pytest + testinfra` tests. This pattern is reused here as the **reference skeleton** for all the unit labs of the training.
