# 🎯 Challenge — Complete CI pipeline for an Ansible collection

## ✅ Objective

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

## 🧩 Stuck?

```bash
dsoxlab hint collections-ci-tests
```

Hints are progressive and **cost points**: the first one points you in the
right direction, the last one unblocks you.

## 🚀 Launch

```bash
# No Ansible run (structural CI/CD lab).
# Local validation of the GitHub Actions workflow:
zizmor labs/collections/ci-tests/challenge/.github/workflows/ansible-test.yml
```

## 🧪 Automated validation

```bash
pytest -v labs/collections/ci-tests/challenge/tests/
```

The pytest test validates:

- GitHub Actions workflow present + actions pinned by SHA + `permissions: {}` + `persist-credentials: false`.
- GitLab CI pipeline present with `sanity` stages and ansible-core × Python matrix.
- At least 2 ansible-core versions in the matrix.
- At least 2 Python versions in the matrix.

## 🧹 Reset

Fully structural lab: no remote cleanup.

## 💡 Going further

- **Renovate** to auto-bump the action SHAs.
- **`ansible-content-actions`**: official composite.
- **Coverage threshold**: `--coverage --coverage-check`.
