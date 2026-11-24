# The role is going public, and it only knows RHEL

## The situation

Your `webserver` role is about to be published, and the first issue is already
predictable. It calls `dnf` directly, writes to `/usr/share/nginx/html` and
assumes the service runs as `nginx`. On Debian the package manager is wrong, the
document root is elsewhere and the user is `www-data`. The role does not work
anywhere else, and worse, the test suite has no way to notice: it only ever
tested the one distribution the author happened to run.

Your mission, from the project directory:

1. Extend the test matrix to **three distributions** across at least two OS
   families, so the suite fails the day portability breaks.
2. Pull the divergent facts (package name, document root, service user) out of
   the tasks and into **per-OS variable files** loaded from the target's own
   detected family.
3. Replace the distribution-specific package calls with the **agnostic** module,
   so the role stops choosing the package manager on the caller's behalf.
4. Verify the **same** role converges on all three platforms, unmodified.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/molecule-scenarios-multi-distro/ (in French)

## 🎯 Challenge: make the webserver role truly multi-distro

### ✅ Mission

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

### 🧩 Stuck?

```bash
dsoxlab hint molecule-scenarios-multi-distro
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

Record in `challenge/solution.sh` the commands you ran. This log
must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/molecule/scenarios-multi-distro/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean molecule-scenarios-multi-distro
```

### 💡 Going further

- Add ubuntu2404 to the matrix: what needs to change in the role?
  (Expected answer: nothing, that is the point.)
- `vars/{{ ansible_distribution }}.yml` as a fine-grained override of
  `{{ ansible_os_family }}.yml`: the first_found pattern.
