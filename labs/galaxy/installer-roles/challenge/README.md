# The same project, two machines, two results

## The situation

The deployment worked in July and fails today, on the same commit. Nothing in the
repository changed: an upstream role published a new major version overnight, and
the project installs it unpinned, so every machine pulls whatever is newest at
the moment it runs. Your laptop, the CI runner and the colleague who onboarded
last week are each running a different codebase from identical Git checkouts.

Your mission, from the project directory:

1. Declare **every** dependency of the project in one manifest: roles from
   Galaxy, roles pulled straight from **Git**, and collections, so nothing is
   installed by folklore any more.
2. **Pin** all of them, and pick the pinning that fits each case: an exact
   version where a surprise is unacceptable, a bounded range where it is not.
3. Distinguish the two install paths, since roles and collections do not land in
   the same place, and neither is versioned by the repository.
4. **Vendor** the one role you cannot afford to lose into the project itself, and
   justify why that one and not the others.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/roles/installer-roles-galaxy/ (in French)

## 🎯 Challenge: write a requirements.yml and actually install it

### ✅ Mission

Two stages, both verified by pytest:

1. **Write** `requirements.yml` (at the lab root, shipped as a skeleton):

   | Expectation | Detail |
   | --- | --- |
   | `roles:` section | at least 2 roles, ALL with a pinned `version:` |
   | Git source | at least 1 role with `src:` pointing to github.com |
   | Galaxy source | at least 1 role without `src:` (resolved via Galaxy) |
   | `collections:` section | at least 1 collection pinned to an EXACT version (X.Y.Z) |

2. **Install** this manifest into the lab (requires the network):

   ```bash
   cd labs/galaxy/installer-roles/
   ansible-galaxy role install -r requirements.yml -p challenge/deps/roles
   ansible-galaxy collection install -r requirements.yml -p challenge/deps/collections
   ```

   Pytest checks that **each declared role is actually present** in
   `challenge/deps/roles/` and that the pinned collection is installed
   **in the exact requested version** (reading MANIFEST.json).

### 🧩 Stuck?

```bash
dsoxlab hint galaxy-installer-roles
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 📓 Command log

Record in `challenge/solution.sh` the install commands
run. This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

### 🧪 Validation

```bash
pytest -v labs/galaxy/installer-roles/challenge/tests/
```

### 🧹 Reset

```bash
dsoxlab clean galaxy-installer-roles
```

### 💡 Going further

- `signatures:` on collections: cryptographic GPG verification.
- `ansible-galaxy install -r ... --force`: force reinstallation.
- Vendor `challenge/deps/` or not? The lockfile debate applied to Ansible.
