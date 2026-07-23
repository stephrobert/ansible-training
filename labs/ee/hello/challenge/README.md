# 🎯 Challenge — Run a first playbook inside an EE

## ✅ Objective

At the lab root, produce 4 files that demonstrate the use of
`ansible-navigator` with an official Execution Environment
(`creator-ee`).

| File | Expectation |
| --- | --- |
| `setup-ee.sh` | Executable. Checks/installs `podman` and `ansible-navigator`. |
| `inventory.yml` | Valid YAML. Hosts `web1.lab` and `db1.lab` in the `all` group, each declaring its `ansible_host` (reachable IP). |
| `ping.yml` | FQCN module `ansible.builtin.ping`. |
| `ansible-navigator.yml` | References the `creator-ee` image in `execution-environment.image:`. |

## 🧩 Stuck?

```bash
dsoxlab hint ee-hello
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
cd labs/ee/hello/
./setup-ee.sh
ansible-navigator run ping.yml -i inventory.yml --mode stdout
```

## 📓 Command log

Record in `challenge/solution.sh` the commands you ran (setup,
navigator run). This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/ee/hello/challenge/tests/
```

The tests actually run `bash -n` on your script,
`ansible-inventory` on your inventory and `ansible-playbook
--syntax-check` on your playbook. Only the run inside the EE (Podman + pull
of creator-ee) stays manual.

## 🧹 Reset

```bash
dsoxlab clean ee-hello
```

## 💡 Going further

- `ansible-navigator --mode interactive`: keyboard-navigable TUI interface
  (`:run`, `:doc`, `:collections`).
- `--pp always`: forces a pull on every run (useful in CI when
  you push the EE often).
- `~/.ansible-navigator.yml`: global config instead of per-project.
