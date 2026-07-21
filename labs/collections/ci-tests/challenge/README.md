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

## 🧩 Hints

### `.github/workflows/ansible-test.yml` skeleton

```yaml
name: Ansible test
on:
  push:
    branches: [main]
  pull_request:

permissions: ???                            # ← global = none

jobs:
  sanity:
    runs-on: ubuntu-24.04
    permissions:
      contents: ???
    strategy:
      fail-fast: ???
      matrix:
        ansible: [???, ???]                 # ← at least 2 versions
        python: [???, ???]                  # ← at least 2 versions
    steps:
      - uses: actions/checkout@???          # ← 40-char SHA
        with:
          path: ???
          persist-credentials: ???

      - uses: actions/setup-python@???      # ← 40-char SHA
        with:
          python-version: "${{ matrix.python }}"

      - run: |
          pip install "https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz"

      - name: ansible-test sanity
        working-directory: ???
        run: ansible-test sanity --docker default -v --color
```

### `.gitlab-ci.yml` skeleton

```yaml
stages:
  - sanity

sanity:
  stage: sanity
  image: python:${PYTHON_VERSION}
  parallel:
    matrix:
      - PYTHON_VERSION: ["???", "???"]
        ANSIBLE_VERSION: ["???", "???"]
  before_script:
    - pip install "https://github.com/ansible/ansible/archive/${ANSIBLE_VERSION}.tar.gz"
    - mkdir -p ansible_collections/student/lab96
  script:
    - cd ansible_collections/student/lab96
    - ???                                    # ← ansible-test command
```

> 💡 **Pitfalls**:
>
> - **`ansible-test`** must be run from the
>   `ansible_collections/<namespace>/<name>/` tree. Outside this tree, it
>   refuses.
> - **`ansible-test sanity`**: lint + import + format. Fast. Run it
>   in pre-commit.
> - **`ansible-test integration`**: real module invocation tests.
>   Requires targets (Docker, Podman, AWS…). Heavier.
> - **`ansible-test units`**: pytest on the modules' Python code.
>   Checks the logic without external dependencies.
> - **Python matrix**: `--python 3.11`, `3.12`, etc. Check compatibility
>   on the targeted Python versions (Ansible 2.18+ requires ≥ 3.11).

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
