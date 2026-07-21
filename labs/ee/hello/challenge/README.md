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

## 🧩 Hints

### Step 1 — `setup-ee.sh` (script to complete)

```bash
cat > setup-ee.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
command -v ??? >/dev/null || sudo dnf install -y ???
command -v ??? >/dev/null || pipx install ???
podman pull ???                            # official creator-ee image
SH
chmod +x setup-ee.sh
```

### Step 2 — `inventory.yml`

```yaml
---
all:
  hosts:
    ???:                                   # web1.lab and db1.lab
    ???:
```

### Step 3 — `ping.yml`

```yaml
---
- name: Hello EE
  hosts: ???
  gather_facts: false
  tasks:
    - name: Pinger
      ansible.builtin.???:
```

### Step 4 — `ansible-navigator.yml`

```yaml
---
ansible-navigator:
  execution-environment:
    image: ???                  # ghcr.io/ansible/creator-ee:latest
    container-engine: ???       # podman (not docker — RHCE 2026 convention)
    pull:
      policy: ???                # 'missing' (pull if absent), 'always' (CI), 'never'
  mode: ???                      # 'stdout' (CI), 'interactive' (TUI)
  logging:
    level: info
```

> 💡 **Pitfalls**:
>
> - **`podman` vs `docker`**: Red Hat recommends Podman (rootless, no
>   daemon). At the EX294 2026, it is `podman` everywhere. Docker works
>   but remains an anti-pattern in the RHEL ecosystem.
> - **`pull.policy: missing`**: pull only if the image is absent
>   locally. **`always`** forces a pull (useful in CI), **`never`**
>   requires the image to be already present (useful offline).
> - **`mode: stdout`** is essential for CI/scripts. The default
>   `interactive` (TUI) blocks in a non-tty script.

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
