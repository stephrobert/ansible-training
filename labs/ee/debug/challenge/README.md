# 🎯 Challenge : diagnose then fix a broken EE

## ✅ Mission

The lab delivers at its root a **broken** Execution Environment
definition (`execution-environment-buggy.yml`, `requirements-buggy.yml`,
`requirements-buggy.txt`). It contains **4 defects** that prevent
obtaining a usable EE. It is up to you to find them: attempt the build, read
the logs, check each dependency, then place a fixed version
in `challenge/`.

Expected deliverables (this is what pytest checks):

| File to create | Expectation |
| --- | --- |
| `challenge/execution-environment.yml` | Complete modern ansible-builder schema, galaxy/python/system sections declared |
| `challenge/requirements.yml` | Only collections that really exist on Galaxy, in FQCN |
| `challenge/requirements.txt` | Only versions that really exist on PyPI |
| `challenge/bindep.txt` | Present, system dependencies declared for the rpm profile |

The buggy files at the root must NOT be modified: they serve
as evidence for the diagnosis.

## 🧩 Stuck?

```bash
dsoxlab hint ee-debug
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 📓 Command log

Record in `challenge/solution.sh` the diagnostic commands you
actually ran (build, podman inspections, galaxy and
pip checks). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/debug/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean ee-debug
```

## 💡 Going further

- `ansible-builder create`: generates the Containerfile without building the image,
  ideal for a quick diagnosis.
- `podman run -it --entrypoint /bin/bash <ee>`: interactive shell in
  the image for inspection.
- `ansible-navigator collections --eei <ee>`: list the collections
  actually embedded.
