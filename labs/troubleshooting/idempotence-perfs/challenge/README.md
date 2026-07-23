# 🎯 Challenge — Refactor a non-idempotent playbook

## ✅ Objective

Write a playbook that **passes the idempotence test**: `changed=0` on the second run. Three operations to chain on `db1.lab`, each **idempotent**:

| # | Action | Recommended module | Idempotence guard |
| --- | --- | --- | --- |
| 1 | Create `/tmp/lab91-marker` with content | `ansible.builtin.shell` | `creates:` |
| 2 | Set `max_connections = 200` in `/tmp/lab91-config.cfg` | `ansible.builtin.lineinfile` | `regexp:` + `create:` |
| 3 | Read the curl version and store it in `/tmp/lab91-curl.txt` | `ansible.builtin.command` + `register` + `copy` | `changed_when: false` on the read |

**Criterion**: the second run of `solution.yml` returns `changed=0`.

## 🧩 Stuck?

```bash
dsoxlab hint troubleshooting-idempotence-perfs
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Running

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/idempotence-perfs/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean troubleshooting-idempotence-perfs
```

## 💡 Going further

- **`ansible-lint --profile production`** detects `command`/`shell` without `changed_when:`.
- **A `ansible-lint` pre-commit hook** in the repo to block regressions.
- **`--check --diff` mode** to preview changes without applying them.
