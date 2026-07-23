# 🎯 Challenge — Combine INI custom facts + Bash script

## ✅ Objective

Drop **two** custom facts on `db1.lab` (one static INI + one dynamic Bash script), then in a playbook **read both** and write a proof file that combines the values.

| Element | Expected value |
| --- | --- |
| Target host | `db1.lab` |
| Custom fact 1 | `/etc/ansible/facts.d/lab14a.fact` (INI, mode `0644`) |
| Custom fact 2 | `/etc/ansible/facts.d/lab14a-uptime.fact` (Bash script, mode `0755`) |
| Produced file | `/tmp/lab14a-custom-facts.txt` |
| Permissions | `0644`, owner `root` |
| Content | Values of the 2 facts (at least 4 lines) |

## 🧩 Stuck?

```bash
dsoxlab hint ecrire-code-custom-facts
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
ansible-playbook labs/ecrire-code/custom-facts/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/ecrire-code/custom-facts/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ecrire-code-custom-facts
```

## 💡 Going further

- **Custom path**: `setup -a "fact_path=/custom/path"` to avoid using the default `/etc/ansible/facts.d/`.
- **`ansible-lint --profile production`** must return green.
