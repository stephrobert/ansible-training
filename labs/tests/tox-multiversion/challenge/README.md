# 🎯 Challenge: write the multi-version tox.ini

## ✅ Mission

The `tox.ini` file is delivered as a **skeleton**. Write the configuration
that tests the `webserver` role on several ansible-core versions.

Expected state (this is what pytest checks):

| Item | Expectation |
| --- | --- |
| `[tox] envlist` | range syntax `ansible2.{...}` covering at least 3 recent ansible-core versions |
| `[testenv]` | `commands` runs `molecule test` |
| `[testenv:ansible-X]` | at least 3 sections, each pinning `ansible-core` in its `deps` |
| `[testenv:lint]` | a separate environment for yamllint + ansible-lint (fail-fast, without spinning up an instance) |

## 🧩 Stuck?

```bash
dsoxlab hint tests-tox-multiversion
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 📓 Command log

When your configuration is ready, record the tox commands you ran in
`challenge/solution.sh`. This log must exist for pytest to
run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/tests/tox-multiversion/challenge/tests/
```

The test parses your tox.ini (section semantics) and, if tox is
installed on the machine, runs `tox --listenvs` to prove the
configuration is accepted by the tool.

## 🧹 Reset

```bash
dsoxlab clean tests-tox-multiversion
```

## 💡 Going further

- `tox -p auto`: run the environments in parallel.
- `tox-uv`: much faster dependency resolution.
- Cross it with the CI matrix from lab 69: local tox, remote GitHub matrix.
