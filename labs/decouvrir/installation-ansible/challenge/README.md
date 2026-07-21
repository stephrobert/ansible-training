# 🎯 Challenge — Installation verification script

## ✅ Objective

Write a Bash script `solution.sh` at the root of **this directory**
(`labs/decouvrir/installation-ansible/challenge/solution.sh`) that:

1. Checks that **`ansible --version`** returns `core 2.18` or higher
2. Checks that the **8 standard binaries** are in the `PATH`
3. Checks that at least **100 modules** are available via `ansible-doc -l`
4. Checks that the **3 key collections** are installed:
   `ansible.posix`, `community.general`, `community.libvirt`
5. **Exit 0** if everything is OK, **exit 1** otherwise with a clear error message

Skeleton to complete:

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Get the ansible-core version (e.g.: "2.18")
#    Tip: `ansible --version | head -1` returns "ansible [core 2.x.y]".
VERSION=$(ansible --version | ???)
# Compare "$VERSION" to 2.18, exit 1 if lower.

# 2. Check that the 8 standard binaries are in the PATH.
#    List: ansible, ansible-playbook, ansible-doc, ansible-galaxy,
#            ansible-vault, ansible-inventory, ansible-config, ansible-console.
for bin in ???; do
    command -v "$bin" >/dev/null || { echo "MISSING $bin"; exit 1; }
done

# 3. Count the available modules via `ansible-doc -l` (>= 100 expected).
COUNT=$(ansible-doc -l 2>/dev/null | wc -l)
[[ ??? ]] || { echo "Trop peu de modules ($COUNT)"; exit 1; }

# 4. Check that the 3 key collections are present via `ansible-galaxy collection list`.
for col in ansible.posix community.general community.libvirt; do
    ansible-galaxy collection list "$col" >/dev/null 2>&1 \
        || { echo "Collection $col manquante"; exit 1; }
done

echo "Installation OK"
```

## 🧪 Validation

The `tests/test_functional.py` script runs your `solution.sh` and checks that
it returns **exit 0** without error:

```bash
pytest -v labs/decouvrir/installation-ansible/challenge/tests/
```

## 🚀 Going further

- Add a **Python version** check (≥ 3.11 expected).
- Display the **detected installation method** (pipx vs dnf vs mise) by
  parsing `ansible --version`.

## 🧹 Reset

To replay the challenge in a clean state:

```bash
dsoxlab clean decouvrir-installation-ansible
```

This target uninstalls/removes what the solution laid down on the managed
nodes (packages, files, services, firewall rules) so that you can replay the
solution from scratch.
