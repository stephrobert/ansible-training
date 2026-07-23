# 🎯 Challenge — Project `ansible.cfg` with `profile_tasks` enabled

## ✅ Objective

Create a lab-level `ansible.cfg` that enables **`profile_tasks`** + forces **`forks=20`** + uses **`stdout_callback = yaml`**, then run a playbook that drops **the output of `ansible-config dump --only-changed`** into a file on `db1.lab`.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab03a-config.txt` |
| Permissions | `0644`, owner `root` |
| Content | Output of `ansible-config dump --only-changed` (≥3 non-empty lines) |
| `ansible.cfg` must contain | `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks` |

## 🧩 Stuck?

```bash
dsoxlab hint decouvrir-configuration-ansible
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
cd labs/decouvrir/configuration-ansible/
ansible-playbook challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/decouvrir/configuration-ansible/challenge/tests/
```

The pytest test validates:

- `/tmp/lab03a-config.txt` exists on `db1.lab` with mode `0644`, owner `root`.
- ≥3 non-empty lines in the content.
- The lab's `ansible.cfg` does contain `forks = 20`, `stdout_callback = yaml`, `callbacks_enabled = ansible.posix.profile_tasks`.

## 🧹 Reset

```bash
dsoxlab clean decouvrir-configuration-ansible
```

## 💡 Going further

- **`ansible-config init --disabled > ansible.cfg`**: generates an exhaustive documented config file.
- **Env variables**: `ANSIBLE_FORKS=50` overrides without touching the file.
- **`ansible-lint`** does not check the content of `ansible.cfg`. To validate the syntax: `ansible-config view`.
