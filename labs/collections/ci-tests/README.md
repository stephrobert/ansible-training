# Lab 96 — CI matrix pipeline `ansible-core` × Python for a collection

> 💡 **Landing directly on this lab without having done the previous ones?**
> Every lab in this repo is **self-contained**. Single prerequisite: the 4 lab
> VMs must respond to the Ansible ping.
>
> ```bash
> cd $ANSIBLE_TRAINING
> ansible all -m ansible.builtin.ping   # → 4 "pong" expected
> ```
>
> If it fails, run `mise install && dsoxlab provision` at the repo root.

## 🧠 Recap

🔗 [**CI pipeline for collections**](https://blog.stephane-robert.info/docs/infra-as-code/gestion-de-configuration/ansible/collections/pipeline-ci/)

A production collection is **tested against several versions** of `ansible-core` and Python to guarantee **backward compatibility**. The 2026 pattern: **GitHub Actions** with an `ansible-core × python` **matrix**, running **`ansible-test sanity`** + **`ansible-test units`** + **`ansible-lint --strict`** in a compliant Docker, with action **SHA pinning** and **`permissions: {}`** at the global level.

This lab provides the complete GitHub Actions workflow (and its GitLab CI equivalent), hardened according to 2026 practices.

## 🎯 Objectives

By the end of this lab, you will know how to:

1. Write a **GitHub Actions workflow** for a collection.
2. Configure a **matrix** `ansible-core stable-2.18 × stable-2.19 × devel × Python 3.11 × 3.12`.
3. Run **`ansible-test sanity --docker`** in the CI.
4. Run **`ansible-test units --docker`** on the Python modules.
5. **Pin** the actions by **SHA** (zizmor compliant).
6. Add **`permissions: {}`** + **`persist-credentials: false`**.
7. Write the **GitLab CI equivalent** with stages `lint`, `sanity`, `units`.

## 🔧 Preparation

```bash
cd $ANSIBLE_TRAINING
ansible all -m ansible.builtin.ping
zizmor --version 2>/dev/null || pipx install zizmor
```

## ⚙️ Target layout

```text
labs/collections/ci-tests/
├── README.md                            ← this file (guided tutorial)
└── challenge/
    ├── README.md                        ← challenge brief
    └── tests/
        └── test_ci.py                   ← structural tests (workflow + .gitlab-ci.yml)
```

The learner writes the `.github/workflows/ansible-test.yml` and `.gitlab-ci.yml` files themselves in `challenge/`.

## 📚 Exercise 1 — Anatomy of a matrix GitHub Actions workflow

```yaml
# .github/workflows/ansible-test.yml
name: Ansible test
on:
  push:
    branches: [main]
  pull_request:

permissions: {}                          # ← global = none

jobs:
  sanity:
    name: sanity (${{ matrix.ansible }} / py${{ matrix.python }})
    runs-on: ubuntu-24.04
    permissions:
      contents: read
    strategy:
      fail-fast: false                   # ← continue even if a combo fails
      matrix:
        ansible:
          - stable-2.18
          - stable-2.19
          - devel
        python:
          - "3.11"
          - "3.12"
    steps:
      - name: Checkout
        uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.2.2
        with:
          path: ansible_collections/student/lab96
          persist-credentials: false

      - name: Setup Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
        with:
          python-version: "${{ matrix.python }}"

      - name: Install ansible-core ${{ matrix.ansible }}
        run: |
          pip install "https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz"

      - name: ansible-test sanity --docker
        working-directory: ansible_collections/student/lab96
        run: |
          ansible-test sanity --docker default -v --color
```

🔍 **Observation**: the **matrix** launches `3 × 2 = 6` jobs in parallel. **`fail-fast: false`** continues even if a combo breaks (useful to see which ones pass). **`permissions: {}`** at the global level, widened per job to the strict minimum.

## 📚 Exercise 2 — SHA pinning of actions

All external actions **must** be pinned by **40-character SHA**:

| Action | SHA (2026 example) | Equivalent tag |
|--------|-------------------|----------------|
| `actions/checkout` | `b4ffde65f46336ab88eb53be808477a3936bae11` | v4.2.2 |
| `actions/setup-python` | `a26af69be951a213d495a4c3e4e4022e16d87065` | v5.6.0 |

🔍 **Crucial observation**: without SHA pinning, an attacker who compromises the `actions/checkout` repo can **repush** the `v4.2.2` tag onto a malicious commit. All pipelines `uses: actions/checkout@v4.2.2` then execute the malicious code. **Zizmor** checks this pattern.

## 📚 Exercise 3 — `persist-credentials: false`

```yaml
- uses: actions/checkout@<SHA>
  with:
    persist-credentials: false           # ← blocks the Git token after the checkout
```

🔍 **Observation**: without this option, the `GITHUB_TOKEN` stays in `.git/config` and can be **exfiltrated** by a later compromised step. **Systematic** pattern on `actions/checkout` in 2026.

## 📚 Exercise 4 — `units` job (Python tests)

```yaml
  units:
    name: units (${{ matrix.ansible }} / py${{ matrix.python }})
    runs-on: ubuntu-24.04
    permissions: { contents: read }
    strategy:
      fail-fast: false
      matrix:
        ansible: [stable-2.18, devel]
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.2.2
        with:
          path: ansible_collections/student/lab96
          persist-credentials: false

      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5.6.0
        with:
          python-version: "${{ matrix.python }}"

      - run: |
          pip install "https://github.com/ansible/ansible/archive/${{ matrix.ansible }}.tar.gz"

      - name: ansible-test units --docker
        working-directory: ansible_collections/student/lab96
        run: |
          ansible-test units --docker default -v --color --python ${{ matrix.python }}
```

🔍 **Observation**: `ansible-test units` runs **pytest** on the collection's `tests/unit/plugins/...` files. **Coverage enabled** by default since 2.16. Block the CI if coverage falls below a threshold with `--coverage --coverage-check`.

## 📚 Exercise 5 — Add `ansible-lint --strict`

```yaml
  lint:
    name: ansible-lint
    runs-on: ubuntu-24.04
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
        with:
          path: ansible_collections/student/lab96
          persist-credentials: false

      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with: { python-version: "3.12" }

      - run: pip install ansible-lint==25.5.0 ansible-core==2.18.1

      - name: ansible-lint --strict --profile production
        working-directory: ansible_collections/student/lab96
        run: ansible-lint --strict --profile production
```

🔍 **Observation**: **`--strict`** promotes warnings to errors. **`--profile production`** enables all the strict rules (FQCN, `no-changed-when` on `command`/`shell`, quoted `mode`, etc.). Combine with `tox-ansible` for a more dynamic matrix.

## 📚 Exercise 6 — Lint the workflow with `zizmor`

```bash
zizmor .github/workflows/ansible-test.yml
```

Automatically detects:

- Actions not pinned by SHA.
- `permissions:` too broad.
- Env variables exposed to the shell without escaping.
- Absence of `persist-credentials: false`.
- Templates with injectable `${{ ... }}`.

🔍 **Observation**: **`zizmor`** is the 2026 reference tool to audit GitHub workflows. Add it as a **pre-commit hook** to block regressions.

## 📚 Exercise 7 — GitLab CI equivalent

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - sanity
  - units

variables:
  ANSIBLE_VERSIONS: "stable-2.18 stable-2.19 devel"
  PYTHON_VERSIONS: "3.11 3.12"

.collection_setup: &collection_setup
  before_script:
    - pip install "https://github.com/ansible/ansible/archive/${ANSIBLE_VERSION}.tar.gz"
    - mkdir -p ansible_collections/student/lab96
    - shopt -s extglob && cp -r !(ansible_collections) ansible_collections/student/lab96/
    - cd ansible_collections/student/lab96

ansible-lint:
  stage: lint
  image: python:3.12
  script:
    - pip install ansible-lint==25.5.0 ansible-core==2.18.1
    - ansible-lint --strict --profile production

sanity:
  stage: sanity
  image: python:${PYTHON_VERSION}
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12"]
        ANSIBLE_VERSION: ["stable-2.18", "stable-2.19", "devel"]
  <<: *collection_setup
  script:
    - ansible-test sanity --docker default -v --color

units:
  stage: units
  image: python:${PYTHON_VERSION}
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12"]
        ANSIBLE_VERSION: ["stable-2.18", "devel"]
  <<: *collection_setup
  script:
    - ansible-test units --docker default -v --color --python ${PYTHON_VERSION}
```

🔍 **Observation**: **`parallel:matrix`** in GitLab CI gives the same effect as the GitHub Actions matrix. **`<<: *collection_setup`** factors the shared `before_script`. Combine with `rules:` to run only on certain modified paths.

## 🔍 Observations to note

- **ansible-core × Python matrix** = 4-6 typical combinations.
- **SHA pinning** of GitHub actions (40 hex characters).
- **`permissions: {}`** at the global level, **`persist-credentials: false`** on checkout.
- **`ansible-test sanity --docker default`** = FQCN + doc + types validation.
- **`ansible-test units --docker`** = pytest on the Python modules.
- **`ansible-lint --strict --profile production`** = maximum quality.
- **Zizmor** lints the workflows.

## 🤔 Reflection questions

1. Why is `fail-fast: false` **recommended** for a test matrix?
2. What is `path: ansible_collections/student/lab96` used for in `actions/checkout`?
3. How do you **block** a GitLab pipeline if **`ansible-test units --coverage`** drops below 80%?
4. What is the advantage of **`tox-ansible`** vs a native GitHub Actions matrix?

## 🚀 Final challenge

See [`challenge/README.md`](challenge/README.md): write a GitHub Actions workflow and a `.gitlab-ci.yml` that pass **`zizmor`** green and run `ansible-test sanity` on at least 2 ansible-core versions.

## 💡 Going further

- **Lab 97**: standalone role → collection migration.
- **Renovate** to auto-bump the action SHAs.
- **`ansible-content-actions`**: official composite GitHub Action.
- **`tox-ansible`**: dynamic matrix.

## 🔍 Linting with `ansible-lint` + `zizmor`

```bash
zizmor labs/collections/ci-tests/challenge/.github/workflows/ansible-test.yml
ansible-lint --profile production labs/collections/ci-tests/
```
