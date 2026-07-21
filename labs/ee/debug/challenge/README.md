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

## 🧩 Hints (method, not answers)

```bash
cd labs/ee/debug/

# 1. Attempt the build and READ the logs, including the warnings at the start
ansible-builder build -f execution-environment-buggy.yml \
    --container-runtime podman --verbosity 3

# 2. A build that "succeeds" proves nothing: what does the EE answer?
podman run --rm local/lab88-buggy:dev ansible --version

# 3. Check each declared collection individually
ansible-galaxy collection install <namespace.collection>:<version>

# 4. Check each Python dependency individually
pip index versions <paquet>
```

Questions to ask yourself: which ansible-builder schema is actually
used when nothing specifies it? Does each declared dependency exist
where it is supposed to be downloaded? What is missing so that the system
dependencies of the collections are installed?

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
