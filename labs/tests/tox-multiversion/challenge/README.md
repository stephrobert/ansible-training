# A bug report from a version you never ran

## The situation

An issue lands on your published role: it fails on `ansible-core` 2.19. You
cannot reproduce it, because your machine runs 2.21 and always has. Your users
do not. Some are pinned to the LTS by their platform team, others are already on
the newest release, and your single-version test suite has been blind to all of
them. Reproducing this by hand means rebuilding a virtualenv per version, and
nobody on the team will do that twice.

Your mission, from the project directory:

1. Declare an environment **per `ansible-core` version** to support, each one
   isolated and pinning its own version, so the versions can never leak into
   each other.
2. Have every environment run the full Molecule cycle against the same role, so
   "it passes" means the same thing on all of them.
3. Make the whole matrix runnable in a **single command**, and a single version
   targetable on demand when you are chasing one specific failure.
4. Read the outcome: a divergence between environments is a portability bug in
   the role, not a flaky test.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/tests-tox-multiversion/ (in French)

## 🎯 Challenge: write the multi-version tox.ini

### ✅ Mission

The `tox.ini` file is delivered as a **skeleton**. Write the configuration
that tests the `webserver` role on several ansible-core versions.

Expected state (this is what pytest checks):

| Item | Expectation |
| --- | --- |
| `[tox] envlist` | range syntax `ansible2.{...}` covering at least 3 recent ansible-core versions |
| `[testenv]` | `commands` runs `molecule test` |
| `[testenv:ansible-X]` | at least 3 sections, each pinning `ansible-core` in its `deps` |
| `[testenv:lint]` | a separate environment for yamllint + ansible-lint (fail-fast, without spinning up an instance) |

### 🧩 Stuck?

```bash
dsoxlab hint tests-tox-multiversion
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

When your configuration is ready, record the tox commands you ran in
`challenge/solution.sh`. This log must exist for pytest to
run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/tests/tox-multiversion/challenge/tests/
```

The test parses your tox.ini (section semantics) and, if tox is
installed on the machine, runs `tox --listenvs` to prove the
configuration is accepted by the tool.

### 🧹 Reset

```bash
dsoxlab clean tests-tox-multiversion
```

### 💡 Going further

- `tox -p auto`: run the environments in parallel.
- `tox-uv`: much faster dependency resolution.
- Cross it with the CI matrix from lab 69: local tox, remote GitHub matrix.
