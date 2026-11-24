# The build says success and the image cannot run Ansible

## The situation

A colleague left you an EE recipe and a problem. The build prints no error worth
stopping for, the image lands on the registry, and the first playbook that tries
to use it dies instantly: there is no `ansible` command inside. Somewhere in
those files, several mistakes are hiding, and the nastiest one is the mistake
that does not fail. The build is not lying to you, you are reading the wrong
line of its output.

Your mission, from the project directory:

1. Try to build the **broken recipe** as it stands, with verbosity turned up, and
   inspect the resulting image rather than trusting the build's exit code.
2. Explain why the image ships **without `ansible-core`** even though the recipe
   plainly asks for it, and find the warning that announced it.
3. Track down the two dependencies that do not exist, one collection and one
   Python version, and prove each is missing at the source rather than blaming
   the network or a proxy.
4. Produce a **fixed set of files**, complete with the system dependencies the
   original forgot, build it, and prove the image now carries what it claims.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/execution-environments/debug-ee-casse/ (in French)

## 🎯 Challenge : diagnose then fix a broken EE

### ✅ Mission

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

### 🧩 Stuck?

```bash
dsoxlab hint ee-debug
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

Record in `challenge/solution.sh` the diagnostic commands you
actually ran (build, podman inspections, galaxy and
pip checks). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/ee/debug/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean ee-debug
```

### 💡 Going further

- `ansible-builder create`: generates the Containerfile without building the image,
  ideal for a quick diagnosis.
- `podman run -it --entrypoint /bin/bash <ee>`: interactive shell in
  the image for inspection.
- `ansible-navigator collections --eei <ee>`: list the collections
  actually embedded.
