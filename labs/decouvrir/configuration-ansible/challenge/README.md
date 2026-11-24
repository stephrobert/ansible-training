# Whose ansible.cfg is actually running?

## The situation

The same playbook takes four minutes for you and eleven for your colleague,
and neither of you can say which `ansible.cfg` Ansible really read: the one in
`/etc`, the one in the home directory, the one at the repo root, or an
environment variable silently overriding them all. Worse, nobody can tell
which task eats the eleven minutes. Guessing stops today.

You work from **control-node.lab** and keep your evidence on `db1.lab`.

Your mission:

1. Write a **project `ansible.cfg`** that raises parallelism to **`forks = 20`**,
   switches output to the **`yaml` callback** and enables **`profile_tasks`** so
   the slow tasks name themselves.
2. Check what is **really active** with `ansible-config dump --only-changed --type all`,
   and understand why your file only wins when the run starts from its
   directory.
3. Archive the proof: drop that dump on `db1.lab` as `/tmp/lab03a-config.txt`,
   owner `root`, mode `0644`.
4. Keep the capture honest: a command that only reads must never report
   `changed`.

The full method is in the companion guide:
https://www.stephane-robert.info/en/docs/infra-as-code/gestion-de-configuration/ansible/decouvrir/ansible-config-fichier/

## 🎯 Challenge — Project `ansible.cfg` with `profile_tasks` enabled

### ✅ Objective

Create a lab-level `ansible.cfg` that enables **`profile_tasks`** + forces **`forks=20`** + uses **`callback_result_format = yaml`**, then run a playbook that drops **the output of `ansible-config dump --only-changed --type all`** into a file on `db1.lab`.

| Item | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Produced file | `/tmp/lab03a-config.txt` |
| Permissions | `0644`, owner `root` |
| Content | Output of `ansible-config dump --only-changed --type all` (≥3 non-empty lines) |
| `ansible.cfg` must contain | `forks = 20`, `callback_result_format = yaml`, `callbacks_enabled = ansible.posix.profile_tasks` |

### 🧩 Stuck?

```bash
dsoxlab hint decouvrir-configuration-ansible
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
cd labs/decouvrir/configuration-ansible/
ansible-playbook challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/decouvrir/configuration-ansible/challenge/tests/
```

The pytest test validates:

- `/tmp/lab03a-config.txt` exists on `db1.lab` with mode `0644`, owner `root`.
- ≥3 non-empty lines in the content.
- The lab's `ansible.cfg` does contain `forks = 20`, `callback_result_format = yaml`, `callbacks_enabled = ansible.posix.profile_tasks`.

### 🧹 Reset

```bash
dsoxlab clean decouvrir-configuration-ansible
```

### 💡 Going further

- **`ansible-config init --disabled > ansible.cfg`**: generates an exhaustive documented config file.
- **Env variables**: `ANSIBLE_FORKS=50` overrides without touching the file.
- **`ansible-lint`** does not check the content of `ansible.cfg`. To validate the syntax: `ansible-config view`.
