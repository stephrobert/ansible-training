# 🎯 Challenge: write a requirements.yml and actually install it

## ✅ Mission

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

## 🧩 Stuck?

```bash
dsoxlab hint galaxy-installer-roles
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 📓 Command log

Record in `challenge/solution.sh` the install commands
run. This log must exist for pytest to run:

```bash
chmod +x challenge/solution.sh
```

## 🧪 Validation

```bash
pytest -v labs/galaxy/installer-roles/challenge/tests/
```

## 🧹 Reset

```bash
dsoxlab clean galaxy-installer-roles
```

## 💡 Going further

- `signatures:` on collections: cryptographic GPG verification.
- `ansible-galaxy install -r ... --force`: force reinstallation.
- Vendor `challenge/deps/` or not? The lockfile debate applied to Ansible.
