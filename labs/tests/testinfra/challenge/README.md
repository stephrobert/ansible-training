# 🎯 Challenge: write the testinfra tests for the webserver role

## ✅ Mission

The `webserver` role and `converge.yml` are delivered. Your job is to write
the verification layer in Python:

| Item | Expectation |
| --- | --- |
| `molecule/default/molecule.yml` | declare the `testinfra` verifier (replace the `???`) |
| `molecule/default/tests/test_webserver.py` | at least 4 `test_*(host)` functions that prove the server state |

The 4 minimal expected proofs:

1. nginx package installed,
2. nginx service started and enabled at boot,
3. socket listening on port 8080,
4. `nginx -t` returns 0 (valid configuration).

## 🧩 Stuck?

```bash
dsoxlab hint tests-testinfra
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 📓 Command log

When your tests are ready, record the commands you ran (`molecule verify`...)
in `challenge/solution.sh`. This log must exist for
pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/tests/testinfra/challenge/tests/
```

The test analyzes your Python file (AST: real test functions
using `host`, real assertions) and checks that pytest can
collect it.

## 🧹 Reset

```bash
dsoxlab clean tests-testinfra
```

## 💡 Going further

- `host.file(...).content_string`: assert on a file's content.
- Parametrize a single test over several packages with `@pytest.mark.parametrize`.
- Compare with the Ansible verifier from lab 62: when to prefer one or the other?
