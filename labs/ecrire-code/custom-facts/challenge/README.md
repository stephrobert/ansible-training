# The host that has to say who owns it

## The situation

Half the fleet has no owner. When a machine misbehaves at 2 a.m., the on-call
engineer has to guess which team to wake, and the only answer lives in a wiki
page a year out of date. The inventory cannot help: it describes what Ansible
manages, not what the machine carries. So the machine is going to say it
itself, and Ansible will read it back at every run, next to the facts it
already collects.

You start with **db1.lab**, from **control-node.lab**.

Your mission:

1. Drop a **static INI custom fact** on db1 declaring the project it belongs
   to, its version, and the team that owns it.
2. Drop a second fact that is an **executable script returning JSON**: the
   things no static file can know, such as the running kernel and the uptime.
3. Get the modes right: a static fact is read, a dynamic one must be
   **executable**. The wrong mode is the classic failure here, and its error
   message will not help you.
4. Re-collect the facts, then read both back through **`ansible_local`** and
   write the proof file on db1.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/ecrire-code/variables-facts/custom-facts/ (in French)

## 🎯 Challenge — Combine INI custom facts + Bash script

### ✅ Objective

Drop **two** custom facts on `db1.lab` (one static INI + one dynamic Bash script), then in a playbook **read both** and write a proof file that combines the values.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Custom fact 1 | `/etc/ansible/facts.d/lab14a.fact` (INI, mode `0644`) |
| Custom fact 2 | `/etc/ansible/facts.d/lab14a-uptime.fact` (Bash script, mode `0755`) |
| Produced file | `/tmp/lab14a-custom-facts.txt` |
| Permissions | `0644`, owner `root` |
| Content | Values of the 2 facts (at least 4 lines) |

### 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-custom-facts
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/custom-facts/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/custom-facts/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ecrire-code-custom-facts
```

### 💡 Going further

- **Custom path**: `setup -a "fact_path=/custom/path"` to avoid using the default `/etc/ansible/facts.d/`.
- **`ansible-lint --profile production`** must return green.
