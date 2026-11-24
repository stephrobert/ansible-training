# Yellow on every run, and nobody reads the recap any more

## The situation

The nightly play reports `changed=14` every single night, on hosts where nothing
has changed for weeks. The tasks redo the work,
they flush caches, and they have trained the team to ignore the recap entirely.
Which is exactly why last Tuesday's real change went unnoticed for three days. On
top of that the play takes eleven minutes, and management has started asking why.

Your mission, from **control-node.lab**:

1. Refactor the three offending operations on **db1.lab** so the play reports
   **`changed=0` on its second pass**: a raw command that must not re-run, a
   config line that must be matched rather than appended, and a read-only lookup
   that has no business reporting a change at all.
2. Prove the fix the only way that counts: run it twice and read the recap.
3. Measure a **baseline** before optimising: name the tasks that actually cost the
   eleven minutes rather than optimising by folklore.
4. Then tune the connection layer: fewer round trips per task, more hosts in
   flight (SSH connection reuse through `ControlPersist` is already on by
   default). Re-measure and state the real gain.

The full method is in the companion guide:
https://www.stephane-robert.info/en/docs/infra-as-code/gestion-de-configuration/ansible/troubleshooting/idempotence-cassee/

## 🎯 Challenge — Refactor a non-idempotent playbook

### ✅ Objective

Write a playbook that **passes the idempotence test**: `changed=0` on the second run. Three operations to chain on `db1.lab`, each **idempotent**:

| # | Action | Recommended module | Idempotence guard |
| --- | --- | --- | --- |
| 1 | Create `/tmp/lab91-marker` with content | `ansible.builtin.shell` | `creates:` |
| 2 | Set `max_connections = 200` in `/tmp/lab91-config.cfg` | `ansible.builtin.lineinfile` | `regexp:` + `create:` |
| 3 | Read the curl version and store it in `/tmp/lab91-curl.txt` | `ansible.builtin.command` + `register` + `copy` | `changed_when: false` on the read |

**Criterion**: the second run of `solution.yml` returns `changed=0`.

### 🧩 Stuck?

```bash
dsoxlab hint troubleshooting-idempotence-perfs
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Running

```bash
ansible-playbook labs/troubleshooting/idempotence-perfs/challenge/solution.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/troubleshooting/idempotence-perfs/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean troubleshooting-idempotence-perfs
```

### 💡 Going further

- **`ansible-lint --profile production`** detects `command`/`shell` without `changed_when:`.
- **A `ansible-lint` pre-commit hook** in the repo to block regressions.
- **`--check --diff` mode** to preview changes without applying them.
