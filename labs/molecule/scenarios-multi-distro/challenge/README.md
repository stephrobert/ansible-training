# 🎯 Challenge: make the webserver role truly multi-distro

## ✅ Mission

The `webserver` role is shipped **mono-distro**: hardcoded `dnf`, hardcoded
RHEL paths and user. It fails on Debian. Your job: make it
portable RHEL + Debian **without duplicating the tasks**, and prove the
portability with a Molecule matrix.

Expected state (this is what pytest checks):

| Item | Expectation |
| --- | --- |
| `tasks/main.yml` | dynamic `include_vars` based on `ansible_os_family`; agnostic `ansible.builtin.package` module (no more `dnf:`/`apt:`); no more hardcoded path or user (`__webserver_*` variables) |
| `vars/RedHat.yml` | completed: package, service, HTML directory and user for the RedHat family |
| `vars/Debian.yml` | completed: same keys, Debian-specific values (HTML directory and user DIFFERENT from RHEL) |
| `molecule.yml` | at least 3 platforms covering the two families |
| Everything | `molecule syntax` passes (pytest actually runs it) |

## 🧩 Stuck?

```bash
dsoxlab hint molecule-scenarios-multi-distro
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 📓 Command log

Record in `challenge/solution.sh` the commands you ran. This log
must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/molecule/scenarios-multi-distro/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean molecule-scenarios-multi-distro
```

## 💡 Going further

- Add ubuntu2404 to the matrix: what needs to change in the role?
  (Expected answer: nothing, that is the point.)
- `vars/{{ ansible_distribution }}.yml` as a fine-grained override of
  `{{ ansible_os_family }}.yml`: the first_found pattern.
