# Your collection ships Python, and Python is where it will break

## The situation

A role is YAML, and YAML mostly survives an upgrade. Your collection ships a
compiled-against-reality Python module, and it breaks on things a role never
notices: a Python version that removed a stdlib call, an `ansible-core` that
changed a module_utils import. Users hit it, you do not, because your machine
runs exactly one combination. And the workflow that is supposed to catch it uses
floating action tags and a token with more rights than it needs.

Your mission, from the project directory:

1. Cross **`ansible-core` versions with Python versions** in a matrix, at least
   two of each, so the combinations your users actually run get tested.
2. Run the collection's own **sanity and unit tests** in containers, so the result
   does not depend on what happens to be installed on the runner.
3. Harden the workflow itself: **no permissions at all globally**, each job
   granted only what it needs, and **no credentials left behind** in the checkout.
4. **Pin every third-party action by commit SHA**: a tag can be moved under you,
   and a supply-chain linter will tell you so.

The full method is in the companion guide:
https://www.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/pipeline-ci/ (in French)

## 🎯 Challenge — Complete CI pipeline for an Ansible collection

### ✅ Objective

Write **two pipeline files** (GitHub Actions + GitLab CI) that pass **`zizmor`** green and run `ansible-test sanity` on **at least 2 versions** of ansible-core.

| Element | Expected value |
| --- | --- |
| GitHub Actions workflow | `.github/workflows/ansible-test.yml` |
| GitLab CI pipeline | `.gitlab-ci.yml` |
| ansible-core versions | at least **2** (e.g. `stable-2.18` + `stable-2.19`) |
| Python versions | at least **2** (e.g. `3.11` + `3.12`) |
| `permissions: {}` | at workflow level |
| `persist-credentials: false` | on `actions/checkout` |
| Pinned actions | by **40-character SHA** |

### 🧩 Stuck?

```bash
dsoxlab hint collections-ci-tests
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

### 🚀 Launch

```bash
# No Ansible run (structural CI/CD lab).
# Local validation of the GitHub Actions workflow:
zizmor labs/collections/ci-tests/challenge/.github/workflows/ansible-test.yml
```

### 🧪 Automated validation

```bash
pytest -v labs/collections/ci-tests/challenge/tests/
```

The pytest test validates:

- GitHub Actions workflow present + actions pinned by SHA + `permissions: {}` + `persist-credentials: false`.
- GitLab CI pipeline present with `sanity` stages and ansible-core × Python matrix.
- At least 2 ansible-core versions in the matrix.
- At least 2 Python versions in the matrix.

### 🧹 Reset

Fully structural lab: no remote cleanup.

### 💡 Going further

- **Renovate** to auto-bump the action SHAs.
- **`ansible-content-actions`**: official composite.
- **Coverage threshold**: `--coverage --coverage-check`.
